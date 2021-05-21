"""
Description : Load data and extract feature for Loglab multi-classification
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

#
# Load raw data from norm file, extract feature and vectorize them
#

import os
import sys
import pickle
import shutil
import importlib
import numpy as np
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
sys.path.append(parentdir)

# Read the log type from the config file
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')

# Import the knowledge base for the corresponding log type
kb = importlib.import_module('oldschool.'+LOG_TYPE+'.knowledgebase')


def load_data(para):
    """ Prepare dataset for the Loglab multi-classification model
    1. Load normalized / structured logs / template library
    2. Load / update (for training only) the revised event id list file
    3. Extract feature and build the vector / matrix

    Arguments
    ---------
    para: the parameters dictionary

    Returns
    -------
    event_matrix: multi-line for training / validation, one line matrix for prediction
    class_vector: vector of target class for each sample
    """

    #------------------------------------------------------------------------------------
    # 1. Load data from train/test norm structured files and template library
    #------------------------------------------------------------------------------------

    # Read columns from normalized / structured log file
    data_df1 = pd.read_csv(para['structured_file'],
                           usecols=['Content', 'EventId', 'EventTemplate'],
                           engine='c', na_filter=False, memory_map=True)
    event_id_logs = data_df1['EventId'].values.tolist()

    # Read EventId from template library file
    data_df2 = pd.read_csv(para['template_lib'], usecols=['EventId'],
                           engine='c', na_filter=False, memory_map=True)
    event_id_templates = data_df2['EventId'].values.tolist()

    #------------------------------------------------------------------------------------
    # 2. Load the vocabulary, aka STIDLE: Shuffled Template Id List Expanded
    #------------------------------------------------------------------------------------

    # Load and update vocabulary. Currently only update with train dataset
    event_id_voc = load_vocabulary(para, event_id_templates)
    #event_id_voc = event_id_templates

    # Count the non-zero event id number in the vocabulary. Suppose at least one zero
    # element exists in the voc.
    voc_size = len(set(event_id_voc)) - 1
    #voc_size = len(set(event_id_voc))

    # Convert event id (hash value) log vector to event index (0 based int) log vector
    # For train dataset the template library / vocabulary normally contain all the
    # possible event ids. For validation / test datasets, they might not retrive some
    # ones. Currently map the unknow event ids to the last index in the vocabulary.
    #event_idx_logs = [event_id_voc.index(tid) for tid in event_id_logs]
    event_idx_logs = []
    for tid in event_id_logs:
        try:
            event_idx_logs.append(event_id_voc.index(tid))
        except ValueError:
            print("Warning: Event ID {} is not in vocabulary!!!".format(tid))
            event_idx_logs.append(para['tmplib_size']-1)

    #------------------------------------------------------------------------------------
    # 3. Feature extraction
    #------------------------------------------------------------------------------------

    # For training or validation, we always handle the multi-sample logs
    if para['train'] or para['metrics_enable']:
        # Load the sample info we stored in logparser module
        with open(para['saminfo_file'], 'rb') as fin:
            sample_info = pickle.load(fin)

        event_matrix, class_vector = extract_feature_multi(para, data_df1, event_id_voc,
                                                           event_id_logs)
    # For prediction, we have to suppose it is always one sample
    else:
        event_matrix, class_vector = extract_feature(para, data_df1, event_id_voc,
                                                     event_id_logs)

    return event_matrix, class_vector


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
        # Initialize shuffled EventId list of templates
        print('Building shuffled EventId list of templates.')

        # We should not get here for prediction
        if not para['train']:
            print("Warning: No existing vocabulary for prediction. Something wrong!")

        # Init STIDLE: Shuffled Template Id List Expanded. Pad ZEROs at the
        # end of event_id_templates to expand the size to TEMPLATE_LIB_SIZE.
        # The event_id_shuffled is a new list copy
        event_id_shuffled = event_id_templates \
                            + ['0'] * (para['tmplib_size'] - len(event_id_templates) -1)

        # Shuffle the expanded list event_id_shuffled in-place
        np.random.default_rng().shuffle(event_id_shuffled)
        # Reserve the last element (no shuffle) with value 'ffffffff'
        event_id_shuffled.append('ffffffff')

        np.save(para['eid_file'], event_id_shuffled)
        np.savetxt(para['eid_file_txt'], event_id_shuffled, fmt="%s")

        return event_id_shuffled

    # Load the existing STIDLE and update it
    print('Loading shuffled EventId list of templates.')
    event_id_shuffled = np.load(para['eid_file']).tolist()

    # We only update STIDLE for train dataset currently
    if para['train']:
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
            # Aggregate all idx of ZERO in STIDLE to a new list copy, then shuffle it
            idx_zero_shuffled = [idx for idx, tid in enumerate(event_id_shuffled) if tid == '0']
            # Shuffle the idx_zero_shuffled in-place
            np.random.default_rng().shuffle(idx_zero_shuffled)
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
        # Find the non ZEROs in EventIdOld that are not equal to the ones in EventId
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


def extract_feature(para, data_df, eid_voc, eid_logs):
    """ Extract feature in a file which we suppose always contains one sample

    Arguments
    ---------
    para: the parameters dictionary
    data_df: data frame contains log content, EventId and EventTemplate
    eid_voc: event id vocabulary
    eid_logs: event ids in raw log file

    Returns
    -------
    event_count_matrix: one line matrix (one sampe) for prediction
    class_vec: empty
    """

    # Initialize the matrix for one sample
    event_count_matrix = np.zeros((1,len(eid_voc)))

    for axis, line in data_df.iterrows():
        log_content_l = line['Content'].strip().split()
        log_event_template_l = line['EventTemplate'].strip().split()
        event_id = line['EventId']

        if len(log_content_l) != len(log_event_template_l):
            continue

        # Traverse all <*> tokens in log_event_template_l and save the index
        # Consider cases like '<*>;', '<*>,', etc. Remove the unwanted ';,' in knowledgebase
        idx_list = [idx for idx, value in enumerate(log_event_template_l) if '<*>' in value]
        #print(idx_list)
        param_list = [log_content_l[idx] for idx in idx_list]
        #print(param_list)

        # Now we can search in the knowledge base for the current log
        typical_log_hit, _, _ = kb.domain_knowledge(event_id, param_list)

        # If current log is hit in KB, add window around the axis
        if typical_log_hit:
            print('current line {} is hit, eid is {}.'.format(axis+1, event_id))

            # Capture the logs within the window. The real window size around typical
            # log is 2*WINDOW_SIZE+1. That is, there are WINDOW_SIZE logs respectively
            # before and after current typical log.
            #

            # The axis part, it is also the typical log
            event_count_matrix[0, eid_voc.index(event_id)] = para['weight']

            # The other part in the window
            for i in range(para['window_size']):
                # The upper part of the window
                if axis - (i+1) >= 0:
                    feature_idx = eid_voc.index(eid_logs[axis-(i+1)])
                    if event_count_matrix[0, feature_idx] == 0:
                        event_count_matrix[0, feature_idx] = 1

                # The under part of the window
                if axis + (i+1) < len(eid_logs):
                    feature_idx = eid_voc.index(eid_logs[axis+(i+1)])
                    if event_count_matrix[0, feature_idx] == 0:
                        event_count_matrix[0, feature_idx] = 1

    # Empty target class for prediction
    class_vec = []

    print_ecm(event_count_matrix, eid_voc)

    return event_count_matrix, class_vec


def extract_feature_multi(para, data_df, eid_voc, eid_logs):
    """ Extract feature in a monolith file which always contains multiple samples
    Arguments
    ---------
    para: the parameters dictionary
    data_df: data frame contains log content, EventId and EventTemplate
    eid_voc: event id vocabulary
    eid_logs: event ids in raw log file

    Returns
    -------
    event_count_matrix: multi-line (samples) for training / validation
    class_vector: vector of target class for each sample
    """
    eid_matrix = []
    class_vec = []
    return eid_matrix, class_vec


def print_ecm(ecm, eid_voc):
    """ Print non-zero values in event count matrix
    """
    for idx, val in enumerate(ecm[0]):
        if val != 0.:
            print("ECM: idx -> {}, eid -> {}, val -> {}".format(idx, eid_voc[idx], val))
