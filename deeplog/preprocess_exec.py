"""
Description : Do dataset preprocessing before feeding DeepLog model
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import shutil
import numpy as np
import pandas as pd
from sklearn.utils import shuffle as scikit_shuffle
from torch.utils.data import DataLoader, Dataset


def load_data(para):
    """ Preprocess dataset before feeding the DeepLog model
    1. Load normalized / structured logs / template library
    2. Load / update (for training only) the revised event id list file
    3. Slice the logs with sliding windows
    4. Construct the pytorch dataloader iterator

    Arguments
    ---------
    para: the parameters dictionary

    Returns
    -------
    data_loader: the pytorch DataLoader object that can be iterated by DeepLog model
    """

    #####################################################################################
    # 1. Load data from train/test norm structured files and template library
    #####################################################################################

    # Read EventId from normalized / structured logs
    data_df1 = pd.read_csv(para['structured_file'], usecols=['EventId'],
                           engine='c', na_filter=False, memory_map=True)
    event_id_logs = data_df1['EventId'].values.tolist()

    # Read EventId from template library file
    data_df2 = pd.read_csv(para['template_lib'], usecols=['EventId'],
                           engine='c', na_filter=False, memory_map=True)
    event_id_templates = data_df2['EventId'].values.tolist()

    # For validation dataset, METRICS_EN is enabled in config file, then read the label vector
    # For other dataset, labels are always ZEROs
    labels = None
    if not para['train'] and para['metrics_enable']:
        data_df3 = pd.read_csv(para['labels_file'], usecols=['Label'],
                               engine='c', na_filter=False, memory_map=True)
        data_df3['Label'] = (data_df3['Label'] != '-').astype(int)
        labels = data_df3['Label'].values.tolist()
    else:
        labels = [0] * len(event_id_logs)

    #####################################################################################
    # 2. Load the vocabulary, aka STIDLE: Shuffled Template Id List Expanded
    #####################################################################################

    event_id_voc = load_vocabulary(para, event_id_templates)
    # Convert event id (hash value) log vector to event index (0 based integer) log vector
    event_idx_logs = [event_id_voc.index(event_id_logs[i]) for i in range(len(event_id_logs))]

    #####################################################################################
    # 3. Slice the logs into sliding windows
    #####################################################################################

    # data_dict:
    # <SeqId> the sequence / window id, aka log line number [0 ~ (logsnum-window_size-1)].
    # <EventSeq> array of [seq_num x window_size] event sequence
    # <Target> the target event index for each window sequence
    # <Label> the label of target event
    data_dict = slice_logs(event_idx_logs, labels, para['window_size'])

    #####################################################################################
    # 4. Feed the pytorch Dataset / DataLoader to get the iterator
    #####################################################################################

    data_loader = DeepLogExecDataset(data_dict, batch_size=para['batch_size'], shuffle=True,
                                     num_workers=para['number_workers']).loader

    return data_loader


def load_vocabulary(para, event_id_templates):
    """ Load the vocabulary, and update it when necessary

    Arguments
    ---------
    para: the parameters dictionary
    event_id_templates: the event id list loaded from template library

    Returns
    -------
    event_id_shuffled: the shuffled version of event id list with a fixed size
    """

    if not os.path.exists(para['eid_file']):
        # Init STIDLE: Shuffled Template Id List Expanded
        # Pad ZEROs at the end of event_id_templates to expand the size to TEMPLATE_LIB_SIZE.
        event_id_templates_ext = event_id_templates \
                                 + ['0'] * (para['tmplib_size'] - len(event_id_templates))

        # Shuffle the expanded list now
        event_id_shuffled = scikit_shuffle(event_id_templates_ext)
        np.save(para['eid_file'], event_id_shuffled)
        np.savetxt(para['eid_file_txt'], event_id_shuffled, fmt="%s")

        return event_id_shuffled

    # Load the existing STIDLE and update it
    print('Loading shuffled EventId list of templates.')
    event_id_shuffled = np.load(para['eid_file']).tolist()

    # We update STIDLE for all dataset including train/validation/test
    # This is different from what we did for the supervised learning

    # Read the EventIdOld column from template library
    data_df = pd.read_csv(para['template_lib'], usecols=['EventIdOld'])
    event_id_templates_old = data_df['EventIdOld'].to_list()
    update_flag = False

    # Case 1):
    # Find the ZERO values in EventIdOld and the corresponding non ZERO EventId
    event_id_old_zero = [event_id_templates[idx] \
                            for idx, tid in enumerate(event_id_templates_old) if tid == '0']

    # There are ZEROs in EventIdOld. It means the corresponding EventId is new
    # No need check the correspinding EventId is non-ZERO
    if len(event_id_old_zero) > 0:
        # Aggregate all idx of ZERO in STIDLE to a new list, then shuffle it
        idx_zero = [idx for idx, tid in enumerate(event_id_shuffled) if tid == '0']
        idx_zero_shuffled = scikit_shuffle(idx_zero)
        # Insert the new EventId to the STIDLE
        updt_cnt = 0
        for idx, tid in enumerate(event_id_old_zero):
            # Make sure no duplicates in the STIDLE
            try:
                event_id_shuffled.index(tid)
            except ValueError:
                event_id_shuffled[idx_zero_shuffled[idx]] = tid
                updt_cnt += 1
        # Set the update flag
        update_flag = True
        print("%d new template IDs are inserted to STIDLE." % updt_cnt)

    # Case 2):
    # Find the non ZERO values in EventIdOld that are not equal to the ones in EventId
    # Replace the old tid with the new one in STIDLE
    updt_cnt = 0
    for tid_old, tid in zip(event_id_templates_old, event_id_templates):
        if tid_old not in('0', tid):
            idx_old = event_id_shuffled.index(tid_old)
            event_id_shuffled[idx_old] = tid
            updt_cnt += 1

    if updt_cnt > 0:
        # Set the update flag
        update_flag = True
        print("%d existing template IDs are updated in STIDLE." % updt_cnt)

    # Case 3):
    # TBD

    # Case 4):
    # TBD

    # Update the STIDLE file
    if update_flag:
        shutil.copy(para['eid_file_txt'], para['eid_file_txt']+'.old')
        np.save(para['eid_file'], event_id_shuffled)
        np.savetxt(para['eid_file_txt'], event_id_shuffled, fmt="%s")

    return event_id_shuffled


def slice_logs(eidx_logs, labels, window_size):
    """ Slice the event index vector in structured file into sequences

    Arguments
    ---------
    eidx_logs: the event index (0 based integer) vector mapping to each log in structured file
    labels: the label for each log in validation dataset
    window_size: the sliding window size, and the unit is log.

    Returns
    -------
    results_dict:
    <SeqId> the sequence / window id, aka log line number [0 ~ (logsnum-window_size-1)].
    <EventSeq> array of [seq_num x window_size] event sequence
    <Target> the target event index for each event sequence
    <Label> the label of target event
    """

    results_lst = []
    print("Slicing the whole logs with window {} ...".format(window_size))

    logsnum = len(eidx_logs)
    i = 0
    while (i + window_size) < logsnum:
        sequence = eidx_logs[i: i + window_size]
        results_lst.append([i, sequence, eidx_logs[i + window_size], labels[i + window_size]])
        i += 1

    # For training, the last window has no target and its label. Simply disgard it.
    # So the total num of sequences are logsnum - window_size

    # Special disposing for the last window
    # --Block comment out start--
    #sequence = eidx_logs[i: i + window_size]
    #sequence += ["#Na"] * (window_size - len(sequence))
    #results_lst.append([i, sequence, "#Na", "#Na"])
    # --end--

    results_df = pd.DataFrame(results_lst, columns=["SeqId", "EventSeq", "Target", "Label"])
    results_dict = {"SeqId": results_df["SeqId"].values,
                    "EventSeq": np.array(results_df["EventSeq"].tolist()),
                    "Target": results_df["Target"].values,
                    "Label": results_df["Label"].values}

    return results_dict


class DeepLogExecDataset(Dataset):
    """ A map-style dataset and embed DataLoader by the way
    https://pytorch.org/docs/stable/data.html#dataset-types
    """
    def __init__(self, data_dict, batch_size=32, shuffle=False, num_workers=1):
        """ Embed the pytorch DataLoader
        """
        self.data_dict = data_dict
        self.keys = list(data_dict.keys())
        self.loader = DataLoader(dataset=self, batch_size=batch_size, shuffle=shuffle,
                                 num_workers=num_workers)

    def __getitem__(self, index):
        """ Return a complete data sample at index
        Here it returns a dict thats represents a complete sample at index
        """
        return {k: self.data_dict[k][index] for k in self.keys}

    def __len__(self):
        """ Return the size of the dataset
        Here it represents the total num of sequences
        """
        return self.data_dict["SeqId"].shape[0]