# Licensed under the MIT License - see License.txt
""" DeepLog module
"""
import os
import logging
import pickle
from typing import List
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, Dataset
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh
from analyzer.modern import ModernBase
from .models import DeepLogExec

__all__ = ["DeepLog"]


log = logging.getLogger(__name__)

class DeepLogExecDataset(Dataset):
    """ A map-style dataset and embed DataLoader by the way
    https://pytorch.org/docs/stable/data.html#dataset-types
    """
    # pylint: disable=super-init-not-called
    def __init__(self, data_dict, batch_size=32, shuffle=False, num_workers=1):
        """ Embed the pytorch DataLoader
        """
        self.data_dict = data_dict
        self.keys = list(data_dict.keys())
        self.loader = DataLoader(dataset=self, batch_size=batch_size, shuffle=shuffle,
                                 num_workers=num_workers)

    def __getitem__(self, index):
        """ Return a complete data sample at index
        Here it returns a dict that represents a complete sample at the
        index. The parameter is sample index, which might not be same as
        the value of self.data_dict["SeqIdx"] because the latter is not
        continous accross session boundaries. See the comments of func
        slice_logs for multi-session. After DataLoader processing, the
        value parts of the dict will be tensors.
        """
        return {k: self.data_dict[k][index] for k in self.keys}

    def __len__(self):
        """ Return the size of the dataset
        Here it represents the total num of sequences
        """
        return self.data_dict["SeqIdx"].shape[0]


class DeepLog(ModernBase):
    """ The class of DeepLog technique """
    # pylint: disable=too-many-arguments
    def __init__(self, df_raws, df_tmplts, segdl: List[tuple],
                 labels: List[int], dbg: bool = False):
        self.model_para: dict = {}
        self.dbg: bool = dbg
        self._segdl: List[tuple] = segdl
        self.exec_model: str = ''
        self.labels: List[int] = labels
        self.load_para()

        ModernBase.__init__(self, df_raws, df_tmplts)


    def load_para(self):
        """ Load/Update model parameters """
        self.model_para['group'] = GC.conf['deeplog']['para_group']
        self.model_para['win_size'] = GC.conf['deeplog']['window_size']
        self.model_para['batch_size'] = GC.conf['deeplog']['batch_size']
        self.model_para['num_epochs'] = GC.conf['deeplog']['num_epochs']
        self.model_para['hidden_size'] = GC.conf['deeplog']['hidden_size']
        self.model_para['topk'] = GC.conf['deeplog']['topk']
        self.model_para['num_dir'] = GC.conf['deeplog']['num_dir']
        self.model_para['num_workers'] = GC.conf['deeplog']['num_workers']
        self.model_para['device'] = GC.conf['deeplog']['device']
        self.exec_model = os.path.join(dh.PERSIST_DATA,
                          'deeplog_exec_model_'+str(self.model_para['group'])+'.pt')


    def load_data(self):
        """
        Extract features, vectoring, and compose data matrix.
        1. Load normalized/structured logs & template library
        2. Load/Update (for training only) the vocab file
        3. Slice the logs with sliding windows

        Arguments
        ---------
        para: the parameters dictionary

        Returns
        -------
        data_dict:
        <SeqIdx> the sequence / sample idx
        <EventSeq> array of [seq_num x window_size] event sequence
        <Target> the target event index for each event sequence
        <Label> the label of target event
        voc_size: the number of non zero event id in the vocabulary
        """

        # --------------------------------------------------------------
        # Load data from parser or files
        # --------------------------------------------------------------
        event_id_logs: List[str] = self._df_raws['EventId'].tolist()
        event_id_lib: List[str] = self._df_tmplts['EventId'].tolist()

        # For validation, METRICS_EN is enabled in config file, and then
        # read label vector. For other dataset, labels are always ZEROs.
        if not self.training and self.metrics:
            if not GC.conf['general']['aim']:
                with open(self.fzip['labels'], 'rb') as fin:
                    self.labels = pickle.load(fin)
        else:
            self.labels = [0] * len(event_id_logs)

        # --------------------------------------------------------------
        # Load vocab, aka STIDLE: Shuffled Template Id List Expanded
        # --------------------------------------------------------------
        event_id_voc: List[str] = self.load_vocab(dh.VOCAB_DEEPLOG, event_id_lib)
        # event_id_voc = event_id_lib

        # Count the non-zero event id number in the vocabulary. Suppose
        # at least one zero element exists in the voc.
        voc_size = len(set(event_id_voc)) - 1
        # voc_size = len(set(event_id_voc))

        # Convert event id (hash value) log vector to event index (0
        # based) log vector. For training data the template library/
        # vocabulary normally contain all the possible event ids. For
        # validation/test data, they might not retrive some ones. Map
        # the unknow event ids to the last index in the vocabulary.
        event_idx_logs = []
        for tid in event_id_logs:
            try:
                event_idx_logs.append(event_id_voc.index(tid))
            except ValueError:
                print("Warning: Event ID {} is not in vocabulary!!!".format(tid))
                event_idx_logs.append(self.libsize-1)

        # --------------------------------------------------------------
        # Extract features
        # --------------------------------------------------------------

        # For train or validation, we always handle multi-session logs
        if self.training or self.metrics:
            # Load the session vector we get from preprocess module
            if not GC.conf['general']['aim']:
                with open(self.fzip['segdl'], 'rb') as fin:
                    self._segdl = pickle.load(fin)

            data_dict = self.slice_logs_multi(event_idx_logs, self.labels,
                                              self.model_para['win_size'],
                                              self._segdl, self.training)
        # For prediction, we need to suppose it is always one session
        else:
            data_dict = self.slice_logs(event_idx_logs, self.labels,
                                        self.model_para['win_size'])

        # data_dict:
        # <SeqIdx> the sequence index
        # <EventSeq> array of [seq_num x window_size] event sequence
        # <Target> the target event index for each window sequence
        # <Label> the label of target event
        return data_dict, voc_size


    @staticmethod
    def slice_logs(eidx_logs, labels, win_size):
        """ Slice event index vector in structured data into sequences

        Note
        ----
        This is single-session logs version, used by prediction only

        Arguments
        ---------
        eidx_logs: event index (0 based int) vector mapping to each log
                   in structured data
        labels: the label for each log in validation dataset
        win_size: the window size, aka. sequence length

        Returns
        -------
        results_dict:
        <SeqIdx> the sequence / sample idx,
                 aka. log line number [0 ~ (logsnum-win_size-1)]
        <EventSeq> array of [seq_num x win_size] event sequence
        <Target> the target event index for each event sequence
        <Label> the label of target event
        """

        results_lst = []
        print("Slicing the single-session logs with window {} ...".format(win_size))

        logsnum = len(eidx_logs)
        i = 0
        while (i + win_size) < logsnum:
            sequence = eidx_logs[i: i + win_size]
            results_lst.append([i, sequence, eidx_logs[i + win_size], labels[i + win_size]])
            i += 1

        # For training, the last window has no target and its label.
        # Simply disgard it. So the total num of sequences equals
        # logsnum - window_size

        results_df = pd.DataFrame(results_lst, columns=["SeqIdx", "EventSeq", "Target", "Label"])
        results_dict = {"SeqIdx": results_df["SeqIdx"].to_numpy(dtype='int32'),
                        "EventSeq": np.array(results_df["EventSeq"].tolist(), dtype='int32'),
                        "Target": results_df["Target"].to_numpy(dtype='int32'),
                        "Label": results_df["Label"].to_numpy(dtype='int32')}

        return results_dict


    @staticmethod
    def slice_logs_multi(eidx_logs, labels, win_size, session_vec, no_metrics):
        """ Slice event index vector in structured file into sequences

        Note
        ----
        This is multi-session logs version, which is used by train or
        validation. This version must also be capable of handling the
        case of one session only.

        Arguments
        ---------
        eidx_logs: event index (0 based int) vector mapping to each log
                   in structured file
        labels: the label for each log in validation dataset
        win_size: the sliding window size, and the unit is log
        session_vec: session vector where each element is session size
        no_metrics: do not consider metrics

        Returns
        -------
        results_dict:
        <SeqIdx> the sequence / sample idx. This is different from
                 single-file logs version.
        <EventSeq> array of [seq_num x window_size] event sequence
        <Target> the target event index for each event sequence
        <Label> the label of target event
        """

        results_lst = []
        print("Slicing the multi-session logs with window {} ...".format(win_size))

        session_offset = 0

        for _, session_size in enumerate(session_vec):
            # The window only applies in each session and do not cross
            # the session boundary. The SeqIdx is not necessary to be
            # continuous with step one across sessions. We did not use
            # the SeqIdx field in the later train/validate/predict. For
            # simplicity, the SeqIdx will be reset to 0 to count again
            # when across the session boundary. Change this behavior if
            # we want to utilize the sequence or sample index across
            # multiple sessions.
            i = 0
            while (i + win_size) < session_size:
                sequence = eidx_logs[i + session_offset: i + session_offset + win_size]
                # The target word label. It is always 0 for training.
                seq_label = labels[i + session_offset + win_size]

                if not no_metrics:
                    # Check every word in the sequence as well as the
                    # target label.
                    seq_labels = labels[i + session_offset: i + session_offset + win_size + 1]
                    if seq_labels.count(1) > 0:
                        seq_label = 1

                results_lst.append([i, sequence, eidx_logs[i + session_offset + win_size],
                                    seq_label])
                i += 1
            # The session first log offset in the concatenated monolith
            session_offset += session_size

        results_df = pd.DataFrame(results_lst, columns=["SeqIdx", "EventSeq", "Target", "Label"])
        results_dict = {"SeqIdx": results_df["SeqIdx"].to_numpy(dtype='int32'),
                        "EventSeq": np.array(results_df["EventSeq"].tolist(), dtype='int32'),
                        "Target": results_df["Target"].to_numpy(dtype='int32'),
                        "Label": results_df["Label"].to_numpy(dtype='int32')}

        return results_dict


    # pylint: disable=too-many-locals
    def evaluate_core(self, model, data_loader, device):
        """ The evaluate core
        """
        _anomaly_pred = []
        # _anomaly_debug = []
        _t_p = _t_n = _f_p = _f_n = 0
        model.eval()
        batch_cnt = len(data_loader)

        with torch.no_grad():
            # Progress bar
            pbar = tqdm(total=batch_cnt, unit='Batches', disable=False, ncols=0)
            for batch_in in data_loader:
                seq = batch_in['EventSeq'].clone().detach()\
                      .view(-1, self.model_para['win_size'], 1).to(device)
                output = model(seq)
                # pred_prob = output.softmax(dim=-1)
                # pred_sort = torch.argsort(pred_prob, 1, True)
                pred_sort = torch.argsort(output, 1, True)
                bt_size = pred_sort.size(0)
                # topk_val = torch.narrow(pred_sort, 1, 0, 10)
                # print('debug topk1:', topk_val)
                seq_pred_sort = pred_sort.tolist()
                seq_target = batch_in['Target'].tolist()
                seq_label = batch_in['Label'].tolist()
                # topk_lst = []
                for i in range(bt_size):
                    # topk_lst.append(seq_pred_sort[i].index(seq_target[i]))
                    top_idx = seq_pred_sort[i].index(seq_target[i])
                    if seq_label[i] == 1:
                        if top_idx >= self.model_para['topk']:
                            _t_p += 1
                            _anomaly_pred.append(1)
                        else:
                            _f_n += 1
                            _anomaly_pred.append(0)
                    else:
                        if top_idx >= self.model_para['topk']:
                            _anomaly_pred.append(1)
                            # _anomaly_debug.append(top_idx)
                            _f_p += 1
                        else:
                            _anomaly_pred.append(0)
                            _t_n += 1

                pbar.update(1)
                # print('debug topk2:', topk_lst)
            # print(_anomaly_debug)
            pbar.close()

        return _t_p, _f_p, _t_n, _f_n, _anomaly_pred


    def train_core(self, model, data_loader, device):
        """ The trining core.
        """
        # Select the loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters())

        model.train()
        batch_cnt = len(data_loader)
        for epoch in range(self.model_para['num_epochs']):
            epoch_loss = 0

            # Progress bar
            pbar = tqdm(total=batch_cnt, unit='Batches', disable=False, ncols=0)
            for batch_in in data_loader:
                # Forward pass
                # Each batch is a dict in the dataloader, in which the
                # value is tensor. The batch_in['EventSeq'] is a 2-D
                # tensor (batch_size x seq_len). The tensor of the input
                # sequences to model should be 3-Dimension as below:
                # (batch_size x seq_len x input_size).
                seq = batch_in['EventSeq'].clone().detach()\
                      .view(-1, self.model_para['win_size'], 1).to(device)
                output = model(seq)
                # The output is 2-D tensor (batch_size x num_classes)
                # The batch_in['Target'] is a 1-D tensor (batch_size)
                # Target (class index) should be in [0, num_classes-1]
                loss = criterion(output, batch_in['Target'].long().view(-1).to(device))

                # Backward pass and optimize
                optimizer.zero_grad()
                loss.backward()
                epoch_loss += loss.item()
                optimizer.step()

                pbar.update(1)

            pbar.close()
            epoch_loss = epoch_loss / batch_cnt
            print("Epoch {}/{}, train loss: {:.5f}"
                  .format(epoch+1, self.model_para['num_epochs'], epoch_loss))


    def train(self):
        """ Train model.
        """
        print("===> Start training the execution path model ...")

        #
        # 1. Load data from train norm structured dataset
        #
        self.load_para()
        train_data_dict, voc_size = self.load_data()
        voc_size = self.libsize

        #
        # 2. Feed pytorch Dataset/DataLoader to get the iterator/tensors
        #
        train_data_loader = DeepLogExecDataset(
            train_data_dict, batch_size=self.model_para['batch_size'],
            shuffle=True, num_workers=self.model_para['num_workers']).loader

        #
        # 3. Build DeepLog Model for Execution Path Anomaly Detection
        #
        device = torch.device(
            'cuda' if self.model_para['device'] != 'cpu' and torch.cuda.is_available() else 'cpu')

        model = DeepLogExec(
            device, num_classes=voc_size, hidden_size=self.model_para['hidden_size'],
            num_layers=2, num_dir=self.model_para['num_dir'])

        #
        # 4. Start training the model
        #
        self.train_core(model, train_data_loader, device)

        # Evaluate itself
        t_p, f_p, t_n, f_n, _ = \
            self.evaluate_core(model, train_data_loader, device)

        print('Train Dataset Validation ==> TP: {}, FP: {}, TN: {}, FN: {}'
              .format(t_p, f_p, t_n, f_n))

        #
        # 5. Serialize the model
        #
        torch.save(model.state_dict(), self.exec_model)


    def evaluate(self):
        """ Validate model.
        """
        print("===> Start validating the execution path model ...")

        #
        # 1. Load data from test norm structured dataset
        #
        self.load_para()
        test_data_dict, voc_size = self.load_data()
        voc_size = self.libsize
        # print(test_data_dict['EventSeq'])
        # print(test_data_dict['Target'])

        #
        # 2. Feed pytorch Dataset/DataLoader to get the iterator/tensors
        #
        test_data_loader = DeepLogExecDataset(
            test_data_dict, batch_size=self.model_para['batch_size'],
            shuffle=False, num_workers=self.model_para['num_workers']).loader

        #
        # 3. Load deeplog_exec model
        #
        device = torch.device(
            'cuda' if self.model_para['device'] != 'cpu' and torch.cuda.is_available() else 'cpu')

        model = DeepLogExec(
            device, num_classes=voc_size, hidden_size=self.model_para['hidden_size'],
            num_layers=2, num_dir=self.model_para['num_dir'])

        model.load_state_dict(torch.load(self.exec_model))

        #
        # 4. Validate the test data
        #
        print("Validating...")
        t_p, f_p, t_n, f_n, _ = \
            self.evaluate_core(model, test_data_loader, device)

        print('Test Dataset Validation  ==> TP: {}, FP: {}, TN: {}, FN: {}'
              .format(t_p, f_p, t_n, f_n))

        # Calc the metrics for dataset with anomalies
        if t_p + f_p != 0 and t_p + f_n != 0:
            precision = 100 * t_p / (t_p + f_p)
            recall = 100 * t_p / (t_p + f_n)
            f_1 = 2 * precision * recall / (precision + recall)

            print('Test Dataset Validation  ==>',
                  'Precision: {:.2f}%, Recall: {:.2f}%, F1: {:.2f}%'
                  .format(precision, recall, f_1))


    def predict(self):
        """ Predict using mdoel.
        """
        print(self.dbg)
