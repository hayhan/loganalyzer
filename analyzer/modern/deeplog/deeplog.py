# Licensed under the MIT License - see LICENSE.txt
""" DeepLog module
"""
import os
import logging
import pickle
from typing import List
from importlib import import_module
import numpy as np
import pandas as pd
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh
from analyzer.modern import ModernBase
from .models import DeepLogExec

# Import the knowledge base for the corresponding log type
kb = import_module("analyzer.oldschool." + dh.LOG_TYPE + ".knowledgebase")


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
        self.loader = DataLoader(dataset=self, batch_size=batch_size,
                                 shuffle=shuffle, num_workers=num_workers)

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
    def __init__(self, df_raws, df_tmplts, dbg: bool = False):
        self.model_para: dict = {}
        self._segdl: List[int] = []
        self._labels: List[int] = []
        self.exec_model: str = ''

        self.load_para()
        self.kbase = kb.Kb()

        ModernBase.__init__(self, df_raws, df_tmplts, dbg)

    @property
    def segdl(self):
        """ Get the segment info """
        return self._segdl

    @segdl.setter
    def segdl(self, segdl: List[int]):
        """ Set the segment info """
        self._segdl = segdl

    @property
    def labels(self):
        """ Get the label vector in norm data """
        return self._labels

    @labels.setter
    def labels(self, labels: List[int]):
        """ Set the label vector in norm data """
        self._labels = labels

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
        self.model_para['one_hot'] = GC.conf['deeplog']['one_hot']
        self.exec_model = os.path.join(
            dh.PERSIST_DATA, 'deeplog_exec_model_'+str(self.model_para['group'])+'.pt'
        )

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
        <EventSeq> array of index, [seq_num x window_size]
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
                    self._labels = pickle.load(fin)
        else:
            self._labels = [0] * len(event_id_logs)

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
        # based) log vector. For training data, the template library/
        # vocabulary normally contain all the possible event ids. For
        # validation/test data, they probably miss some unknown ones.
        # Map the unknown events to the last index in the vocabulary.
        event_idx_logs = []
        new_eids = set()
        for tid in event_id_logs:
            try:
                event_idx_logs.append(event_id_voc.index(tid))
            except ValueError:
                new_eids.add(tid)
                event_idx_logs.append(self.libsize-1)

        if len(new_eids) != 0:
            for ele in new_eids:
                log.warning("Warning: Event ID %s is not in vocabulary!!!", ele)

        # --------------------------------------------------------------
        # Extract features
        # --------------------------------------------------------------

        # For train or validation, we always handle multi-session logs
        if self.training or self.metrics:
            # Load the session vector we get from preprocess module
            if not GC.conf['general']['aim']:
                with open(self.fzip['segdl'], 'rb') as fin:
                    self._segdl = pickle.load(fin)

            data_dict = self.slice_logs_multi(event_idx_logs)
        # For prediction, we need to suppose it is always one session
        else:
            data_dict = self.slice_logs(event_idx_logs)

        # data_dict:
        # <SeqIdx> the sequence index
        # <EventSeq> array of index, [seq_num x window_size]
        # <Target> the target event index for each window sequence
        # <Label> the label of target event
        return data_dict, voc_size

    def slice_logs(self, eidx_logs):
        """ Slice event index vector in structured data into sequences

        Note
        ----
        This is single-session logs version, used by prediction only

        Arguments
        ---------
        eidx_logs: event index (0 based int) vector mapping to each \
                   log in structured data

        Returns
        -------
        data_dict:
        <SeqIdx> the sequence / sample idx, \
                 aka. log line number [0 ~ (logsnum-win_size-1)]
        <EventSeq> array of index, [seq_num x window_size]
        <Target> the target event index for each event sequence
        <Label> the label of target event
        """

        win_size = self.model_para['win_size']
        data_lst = []
        print(f"Slicing the single-session logs with window {win_size} ...")

        logsnum = len(eidx_logs)
        i = 0
        while (i + win_size) < logsnum:
            sequence = eidx_logs[i: i + win_size]
            data_lst.append(
                [i, sequence, eidx_logs[i + win_size], self._labels[i + win_size]]
            )
            i += 1

        # For training, the last window has no target and its label.
        # Simply disgard it. So the total num of sequences equals
        # logsnum - window_size

        data_df = pd.DataFrame(data_lst, columns=["SeqIdx", "EventSeq", "Target", "Label"])
        data_dict = {
            "SeqIdx": data_df["SeqIdx"].to_numpy(dtype='int32'),
            "EventSeq": np.array(data_df["EventSeq"].tolist(), dtype='int32'),
            "Target": data_df["Target"].to_numpy(dtype='int32'),
            "Label": data_df["Label"].to_numpy(dtype='int32')
        }

        return data_dict

    def slice_logs_multi(self, eidx_logs):
        """ Slice event index vector in structured file into sequences

        Note
        ----
        This is multi-session logs version, which is used by train or
        validation. This version must also be capable of handling the
        case of one session only.

        Arguments
        ---------
        eidx_logs: event index (0 based int) vector mapping to each \
                   log in structured data

        Returns
        -------
        data_dict:
        <SeqIdx> the sequence / sample idx. This is different from
                 single-file logs version.
        <EventSeq> array of index, [seq_num x window_size]
        <Target> the target event index for each event sequence
        <Label> the label of target event
        """

        win_size = self.model_para['win_size']
        data_lst = []
        print(f"Slicing the multi-session logs with window {win_size} ...")

        session_offset = 0

        for _, session_size in enumerate(self._segdl):
            # The window only applies in each session and doesn't cross
            # session boundary. SeqIdx no needs to be continuous with
            # with step one across sessions. We do not use SeqIdx field
            # in the later train/validate/predict. For simplicity, the
            # SeqIdx will reset to 0 to count again when across session
            # boundary. Change this behavior if we want to utilize the
            # sequence or sample index across multiple sessions.
            i = 0
            while (i + win_size) < session_size:
                sequence = eidx_logs[i + session_offset: i + session_offset + win_size]
                # The target word label. It is always 0 for training.
                seq_label = self._labels[i + session_offset + win_size]

                # For validation, aka training==false && metric==true
                if not self.training:
                    # Check each word in the seq as well as target label
                    seq_labels = \
                        self._labels[i + session_offset: i + session_offset + win_size + 1]
                    if seq_labels.count(1) > 0:
                        seq_label = 1

                data_lst.append(
                    [i, sequence, eidx_logs[i + session_offset + win_size], seq_label]
                )
                i += 1
            # The session first log offset in the concatenated monolith
            session_offset += session_size

        data_df = pd.DataFrame(data_lst, columns=["SeqIdx", "EventSeq", "Target", "Label"])
        data_dict = {
            "SeqIdx": data_df["SeqIdx"].to_numpy(dtype='int32'),
            "EventSeq": np.array(data_df["EventSeq"].tolist(), dtype='int32'),
            "Target": data_df["Target"].to_numpy(dtype='int32'),
            "Label": data_df["Label"].to_numpy(dtype='int32')
        }

        return data_dict

    def para_anomaly_det(self, content, eid, template):
        """ Detect the parameter anomaly by using the OSS

        Arguments
        ---------
        content: the content of the log
        eid: the event id of the log
        template: the template of the log

        Returns
        -------
        True/False: Anomaly is detected (True) or not (False)
        """
        # Convert the log string into token list
        content_ln = content.strip().split()
        template_ln = template.strip().split()

        if len(content_ln) != len(template_ln):
            return False

        # Traverse all <*> tokens in log_event_tmplt_l and save the
        # index. Consider cases like '<*>;', '<*>,', etc. Remove the
        # unwanted ';,' in knowledgebase.
        idx_list = [idx for idx, value in enumerate(template_ln) if '<*>' in value]
        # print(idx_list)
        param_list = [content_ln[idx] for idx in idx_list]
        # print(param_list)

        # Now we can search in the knowledge base for the current log
        severity, _, _ = self.kbase.domain_knowledge(eid, param_list)

        return severity != 'info'

    def load_oss_data(self):
        """ Load data for OSS para value detection

        Arguments
        ---------

        Returns
        -------
        content_lst: content list from norm struct data
        eid_lst: event id list from norm struct data
        template_lst: template list from nnorm struct data
        """
        # If messed logs recovering enabled, read the content from the
        # original (aka. the 1st parsing result) structured norm.
        if self.rcv:
            if GC.conf['general']['aim']:
                content_lst = self._df_raws_o['Content'].tolist()
            else:
                content_lst = pd.read_csv(self.fzip['struct'], usecols=['Content'],
                                    engine='c', na_filter=False, memory_map=True)
        else:
            content_lst = self._df_raws['Content'].tolist()

        eid_lst = self._df_raws['EventId'].tolist()
        template_lst = self._df_raws['EventTemplate'].tolist()

        return content_lst, eid_lst, template_lst

    def get_ready(self, is_shuffle=True):
        """ Get work ready before training/validation/prediction
        """
        #
        # Load data from train/test norm structured dataset per config
        #
        self.load_para()
        data_dict, voc_size = self.load_data()
        voc_size = self.libsize

        #
        # Feed pytorch Dataset/DataLoader to get the iterator/tensors
        #
        data_loader = DeepLogExecDataset(
            data_dict, batch_size=self.model_para['batch_size'],
            shuffle=is_shuffle, num_workers=self.model_para['num_workers']
        ).loader

        #
        # Build DeepLog Model for Execution Path Anomaly Detection
        #
        device = torch.device(
            'cuda' if self.model_para['device'] != 'cpu' and torch.cuda.is_available() else 'cpu'
        )

        if self.model_para['one_hot']:
            input_dim = self.libsize
        else:
            input_dim = 1

        model = DeepLogExec(
            device, num_classes=voc_size, input_size=input_dim,
            hidden_size=self.model_para['hidden_size'],
            num_layers=2, num_dir=self.model_para['num_dir']
        )

        return model, data_loader, device

    # pylint: disable=too-many-locals
    def predict_core(self, model, data_loader, device, mnp_vec):
        """ The predict core
        """
        # Data for parameter value anomaly detection
        content_lst, eid_lst, template_lst = self.load_oss_data()

        j = 0
        anomaly_pred = []
        anomaly_line = []
        model.eval()
        with torch.no_grad():
            for batch_in in data_loader:
                # print(batch_in['EventSeq'])
                seq = self.d2_d3(batch_in['EventSeq'], device)
                output = model(seq)
                # pred_prob = output.softmax(dim=-1)
                # pred_sort = torch.argsort(pred_prob, 1, True)
                pred_sort = torch.argsort(output, 1, True)
                bt_size = pred_sort.size(0)
                # topk_val = torch.narrow(pred_sort, 1, 0, 10)
                # print('debug topk1:', topk_val)
                seq_pred_sort = pred_sort.tolist()
                seq_target = batch_in['Target'].tolist()
                # topk_lst = []
                for i in range(bt_size):
                    # topk_lst.append(seq_pred_sort[i].index(seq_target[i]))
                    # The log (line, 0-based) index of anomaly in norm
                    norm_idx = i+self.model_para['win_size']+j*self.model_para['batch_size']
                    top_idx = seq_pred_sort[i].index(seq_target[i])

                    if top_idx >= self.model_para['topk']:
                        # Save each log state from line (WIN_SIZE+1)
                        anomaly_pred.append(1)
                        # Save anomaly log index of norm data
                        anomaly_line.append(norm_idx)
                    else:
                        # Integrate OSS as para value anomaly detection
                        if self.para_anomaly_det(content_lst[mnp_vec[norm_idx]],
                                                 eid_lst[norm_idx], template_lst[norm_idx]):
                            anomaly_pred.append(1)
                            anomaly_line.append(norm_idx)
                        else:
                            anomaly_pred.append(0)
                # print('debug topk2:', topk_lst)
                j += 1

        # print(anomaly_pred)
        # print(anomaly_line)
        # print(len(anomaly_line))
        return anomaly_line

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
                seq = self.d2_d3(batch_in['EventSeq'], device)
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
                seq = self.d2_d3(batch_in['EventSeq'], device)

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
            print(f"Epoch {epoch+1}/{self.model_para['num_epochs']}, "
                  f"train loss: {epoch_loss:.5f}")

    def d2_d3(self, tensor_2d, device):
        """
        Convert 2-D input tensor to 3-D. Also use input data in scalar
        or one-hot vector based on config setting.

        For scalar, the input_size is 1. For one-hot, the input_size is
        the size of template/vocabulary. Also the element type is float
        in the returned 3-D tensor.

        Note:
        Do the 2-D to 3-D conversion and one-hot vectoring in the batch
        instead of in the whole data set in one shot. The latter will
        consume considerable memory and time.

        Arguments
        ---------
        tensor_2d: the 2-D tensor, [seq_num x win_size]
        device: cpu or gpu

        Returns
        -------
        tensor_3d: the 3-D tensor, [seq_num x win_size x input_size]
        """

        if self.model_para['one_hot']:
            tensor_3d = nn.functional.one_hot(tensor_2d.long(), num_classes=self.libsize)\
                        .float().clone().detach().requires_grad_(True).to(device)
        else:
            tensor_3d = tensor_2d.float().clone().detach().requires_grad_(True)\
                        .view(-1, self.model_para['win_size'], 1).to(device)

        return tensor_3d

    def train(self):
        """ Train model.
        """
        print("===> Start training the execution path model ...")

        # Get everything ready before training
        model, train_data_loader, device = \
            self.get_ready(is_shuffle=True)

        # Start training the model
        self.train_core(model, train_data_loader, device)

        # Evaluate itself
        t_p, f_p, t_n, f_n, _ = \
            self.evaluate_core(model, train_data_loader, device)

        print(f"Train Dataset Validation ==> TP: {t_p}, FP: {f_p}, TN: {t_n}, FN: {f_n}")

        # Serialize the model
        torch.save(model.state_dict(), self.exec_model)

    def evaluate(self):
        """ Validate model.
        """
        print("===> Start validating the execution path model ...")

        # Get everything ready before validation
        model, test_data_loader, device = \
            self.get_ready(is_shuffle=False)

        # Load the model from file
        model.load_state_dict(torch.load(self.exec_model))

        # Validate the test data
        print("Validating...")
        t_p, f_p, t_n, f_n, _ = \
            self.evaluate_core(model, test_data_loader, device)

        print(f"Test Dataset Validation ==> TP: {t_p}, FP: {f_p}, TN: {t_n}, FN: {f_n}")

        # Calc the metrics for dataset with anomalies
        if t_p + f_p != 0 and t_p + f_n != 0:
            precision = 100 * t_p / (t_p + f_p)
            recall = 100 * t_p / (t_p + f_n)
            f_1 = 2 * precision * recall / (precision + recall)

            print(f"Test Dataset Validation ==> "
                  f"Precision: {precision:.2f}%, Recall: {recall:.2f}%, F1: {f_1:.2f}%")

    def predict(self):
        """ Predict using model.
        """
        print("===> Start predicting using the execution path model ...")

        # Get everything ready before prediction
        model, test_data_loader, device = \
            self.get_ready(is_shuffle=False)

        # Load the model from file
        model.load_state_dict(torch.load(self.exec_model))

        # The line mapping between norm and norm pred
        if self.rcv:
            if GC.conf['general']['aim']:
                mnp_vec = self._map_norm_rcv
            else:
                with open(self.fzip['map_norm_rcv'], 'rb') as fin:
                    mnp_vec = pickle.load(fin)
        else:
            mnp_vec = list(range(self._df_raws.shape[0]))

        # Predict the test data
        anomaly_line = self.predict_core(model, test_data_loader, device, mnp_vec)

        # Load the line mapping list between raw and norm test file
        if not GC.conf['general']['aim']:
            with open(self.fzip['map_norm_raw'], 'rb') as fin:
                self._map_norm_raw = pickle.load(fin)

        # Write to file. It is 1-based line num in raw file. Map the
        # anomaly_line in norm file to the raw test data file.
        with open(self.fzip['rst_dlog'], 'w', encoding='utf-8') as fout:
            for item in anomaly_line:
                fout.write(f"{self._map_norm_raw[item]}\n")
