"""
Description : To do feature extractor and create event count matrix
Author      : LogPAI Team, Wei Han <wei.han@broadcom.com>
License     : MIT
"""
import logging
import pandas as pd
import os
import numpy as np
#import re
#import sys
import shutil
from sklearn.utils import shuffle
from datetime import datetime
#from collections import OrderedDict
#from collections import Counter

#curfiledir = os.path.dirname(__file__)
#parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))


def load_data(para, feat_ext_inc=False):
    """ Load normalized / structured logs into train or test dataset

    Arguments
    ---------
    para: the parameters dictionary
    featExt_inc: incrementally update event count matrix

    Returns
    -------
    raw_data: list of (label, time)
    event_mapping_data: a list of event id mapping to each line (log)
    event_id_templates: a list mapping event id to index, e.g. -> 0, 1, ... in templates file
    """

    # Read data from normalized / structured logs
    data_df1 = pd.read_csv(para['structured_file'], usecols=['Time', 'EventId'])
    data_df1['Time'] = pd.to_datetime(data_df1['Time'], format="[%Y%m%d-%H:%M:%S.%f]")
    # Convert timestamp to millisecond unit
    data_df1['Ms_Elapsed'] = ((data_df1['Time']-data_df1['Time'][0]).dt.total_seconds()*1000).astype('int64')

    # If it is normal prediction, init the label vector with ZEROs
    # If train or predict with validating, read the real label vector
    if (para['train'] == False) and (para['extractLabel'] == False):
        data_df1['Label'] = pd.DataFrame(0, index=range(len(data_df1)), columns=['Label'])
    else:
        data_df2 = pd.read_csv(para['labels_file'], usecols=['Label'])
        data_df2['Label'] = (data_df2['Label'] != '-').astype(int)
        data_df1['Label'] = data_df2['Label']

    raw_data = data_df1[['Label','Ms_Elapsed']].values

    event_mapping_data = data_df1['EventId'].values

    # Read EventId from templates
    # Read the template lib for incremental featrureExt / learning
    # Read the template file from results/train or results/test
    # Actually it is not used for test dataset in any cases
    if feat_ext_inc:
        template_lib_loc = para['persist_path']+'template_lib.csv'
        data_df3 = pd.read_csv(template_lib_loc, usecols=['EventId'])
    else:
        data_df3 = pd.read_csv(para['templates_file'], usecols=['EventId'])
    event_id_templates = data_df3['EventId'].to_list()

    #logging.debug(raw_data)
    #logging.debug(event_mapping_data)
    #logging.debug(event_id_templates)
    np.savetxt(para['data_path']+'elapsed_time_vector.csv', data_df1['Ms_Elapsed'].tolist(), fmt="%s")

    # Do not calc the num of logs that are anomalies on test dataset w/o validating
    if not ((para['train'] == False) and (para['extractLabel'] == False)):
        print('The number of anomaly logs is %d, but it requires further processing' % sum(raw_data[:, 0]))
    return raw_data, event_mapping_data, event_id_templates


def add_sliding_window(para, raw_data, event_mapping_data, event_id_templates, feat_ext_inc=False):
    """ Split logs into sliding windows, built an event count matrix and get the corresponding label

    Args:
    --------
    para: the parameters dictionary
    raw_data: list of (label, time)
    event_mapping_data: a list of event id mapping to each line (log)
    event_id_templates: a list mapping event id to index, e.g. -> 0, 1, ... in templates file
    featExt_inc: incrementally update event count matrix

    Returns:
    --------
    event_count_matrix: event count matrix, where each row is an instance (log sequence vector)
    labels: a list of labels, 1 represents anomaly
    """

    # create the directory for saving the sliding windows (start_index, end_index), which can be directly loaded in future running
    #if not os.path.exists(para['window_path']):
        #os.mkdir(para['window_path'])

    log_size = raw_data.shape[0]
    sliding_window_file = para['data_path']+'sliding_'+str(para['window_size'])+'ms_'+str(para['step_size'])+'ms.csv'
    event_id_shuffled_file = para['persist_path']+'event_id_shuffled.npy'
    event_id_shuffled_file_txt = para['persist_path']+'event_id_shuffled.txt'
    event_id_shuffled_file_static = para['persist_path']+'event_id_shuffled_static.npy'
    template_lib_loc = para['persist_path']+'template_lib.csv'

    # Feature extraction incremental update for models that support incremental learning.
    if feat_ext_inc:
        # Shuffle the event_id_templates
        if not os.path.exists(event_id_shuffled_file):
            # Init STIDLE: Shuffled Template Id List Expanded
            # Pad ZEROs at the end of event_id_templates to expand the size to TEMPLATE_LIB_SIZE.
            event_id_templates_ext = event_id_templates + ['0'] * (para['tmplib_size'] - len(event_id_templates))

            # Shuffle the expanded list now
            event_id_shuffled = shuffle(event_id_templates_ext)
            np.save(event_id_shuffled_file, event_id_shuffled)
            np.savetxt(event_id_shuffled_file_txt, event_id_shuffled, fmt="%s")
        else:
            print('Loading shuffled EventId list in templates: incremental update version.')
            event_id_shuffled = np.load(event_id_shuffled_file).tolist()

            # Update STIDLE, aka. event_id_shuffled, ONLY do the update for train dataset
            if para['train'] == True:
                # Read the EventIdOld column from template library
                data_df = pd.read_csv(template_lib_loc, usecols=['EventIdOld'])
                event_id_templates_old = data_df['EventIdOld'].to_list()
                STIDLE_update_flag = False

                # Case 1):
                # Find the ZERO values in EventIdOld and the corresponding non ZERO EventId
                event_id_old_zero = [event_id_templates[idx] \
                                     for idx, tid in enumerate(event_id_templates_old) if tid == '0']

                # There are ZEROs in EventIdOld. It means the corresponding EventId is new
                # No need check the correspinding EventId is non-ZERO
                if len(event_id_old_zero):
                    # Aggregate all idx of ZERO in STIDLE to a new list, then shuffle it
                    idx_zero_STIDLE = [idx for idx, tid in enumerate(event_id_shuffled) if tid == '0']
                    idx_zero_STIDLE_shuffled = shuffle(idx_zero_STIDLE)
                    # Insert the new EventId to the STIDLE
                    new_insert_cnt = 0
                    for idx, tid in enumerate(event_id_old_zero):
                        # Make sure no duplicates in the STIDLE
                        try:
                            event_id_shuffled.index(tid)
                        except:
                            event_id_shuffled[idx_zero_STIDLE_shuffled[idx]] = tid
                            new_insert_cnt += 1
                    # Set the update flag
                    STIDLE_update_flag = True
                    print("%d new template IDs are inserted to STIDLE." % new_insert_cnt)

                # Case 2):
                # Find the non ZERO values in EventIdOld that are not equal to the ones in EventId
                # Replace the old tid with the new one in STIDLE
                updt_cnt = 0
                for tidOld, tidNew in zip(event_id_templates_old, event_id_templates):
                    if tidOld != '0' and tidOld != tidNew:
                        idxOld = event_id_shuffled.index(tidOld)
                        event_id_shuffled[idxOld] = tidNew
                        updt_cnt += 1

                if updt_cnt > 0:
                    # Set the update flag
                    STIDLE_update_flag = True
                    print("%d existing template IDs are updated in STIDLE." % updt_cnt)

                # Case 3):
                # TBD

                # Case 4):
                # TBD

                # Update the STIDLE file
                if STIDLE_update_flag:
                    shutil.copy(event_id_shuffled_file_txt, event_id_shuffled_file_txt+'.old')
                    np.save(event_id_shuffled_file, event_id_shuffled)
                    np.savetxt(event_id_shuffled_file_txt, event_id_shuffled, fmt="%s")
    else:
        # Shuffle the event_id_templates
        #if para['train'] == True:
        if not os.path.exists(event_id_shuffled_file_static):
            event_id_shuffled = shuffle(event_id_templates)
            np.save(event_id_shuffled_file_static, event_id_shuffled)
        else:
            print('Loading shuffled EventId list in templates: static version.')
            event_id_shuffled = np.load(event_id_shuffled_file_static).tolist()

    #=============divide into sliding windows=========#
    start_end_index_list = [] # list of tuples, tuple contains two numbers, which represents the start and end of sliding window
    label_data, time_data = raw_data[:, 0], raw_data[:, 1]
    if not os.path.exists(sliding_window_file) or para['window_rebuild']:
        parse_st = datetime.now()
        # Split into sliding windows
        start_time = time_data[0]
        start_index = 0
        end_index = -1

        # Get the first start, end index, end time
        for cur_time in time_data:
            # Window end (end_time) selects the min if not equal
            if  cur_time <= start_time + para['window_size']:
                end_index += 1
                #end_time = cur_time
            else:
                break
        start_end_pair=tuple((start_index, end_index))
        start_end_index_list.append(start_end_pair)

        # Move the start and end index until next sliding window
        while end_index < log_size - 1:

            prev_win_start = start_index
            for cur_time in time_data[prev_win_start:]:
                # Window start (start_time) selects the max if not equal
                if cur_time < start_time + para['step_size']:
                    start_index += 1
                else:
                    start_time = cur_time
                    break

            end_index = start_index - 1
            curr_win_start = start_index
            for cur_time in time_data[curr_win_start:]:
                # Window end (end_time) selects the min if not equal
                if cur_time <= start_time + para['window_size']:
                    end_index += 1
                    #end_time = cur_time
                else:
                    break

            start_end_pair=tuple((start_index, end_index))
            start_end_index_list.append(start_end_pair)
            #print(start_end_index_list)

            # Snippet below iterates the idx but I dont remember why I didnt use it
            """
            end_time = start_time + para['window_size']
            for i in range(start_index, end_index):
                if time_data[i] < start_time:
                    i+=1
                else:
                    break
            for j in range(end_index, log_size):
                if time_data[j] < end_time:
                    j+=1
                else:
                    break
            start_index = i
            end_index = j
            start_end_pair = tuple((start_index, end_index))
            start_end_index_list.append(start_end_pair)
            """
        inst_number = len(start_end_index_list)
        print('There are {} instances (sliding windows) in this dataset, cost {!s}\n'.format(inst_number, datetime.now()-parse_st))
        np.savetxt(sliding_window_file, start_end_index_list, delimiter=',',fmt='%d')
    else:
        print('Loading start_end_index_list from file')
        start_end_index_list = pd.read_csv(sliding_window_file, header=None).values
        inst_number = len(start_end_index_list)
        print('There are %d instances (sliding windows) in this dataset' % inst_number)

    # Get all the log indexes in each time window by ranging from start_index to end_index
    expanded_indexes_list=[]
    for dummy in range(inst_number):
        index_list = []
        expanded_indexes_list.append(index_list)
    for i in range(inst_number):
        start_index = start_end_index_list[i][0]
        end_index = start_end_index_list[i][1]
        for l in range(start_index, end_index+1):
            expanded_indexes_list[i].append(l)
    logging.debug('All the log idx in each window: {}'.format(expanded_indexes_list))

    #event_mapping_data = [row for row in event_mapping_data]
    #event_mapping_data = list(event_mapping_data)
    event_mapping_data = event_mapping_data.tolist()
    logging.debug('The eventId for each line (log): {}'.format(event_mapping_data))
    # Count the overall num of log events. We can also get it from the *_templates.csv
    event_num = len(list(set(event_mapping_data)))
    print('There are %d log events' %event_num)

    #=============Get labels and event count of each sliding window =========#
    labels = []
    event_count_matrix = np.zeros((inst_number,len(event_id_shuffled)))
    for j in range(inst_number):
        label = 0   # 0 represents success, 1 represents failure
        for k in expanded_indexes_list[j]:
            # Label the instance even if current log might not be in train template lib
            if label_data[k]:
                label = 1
            # Current log EventId, aka. template id
            event_id = event_mapping_data[k]
            # Convert EventId to ZERO based index in shuffed EventId list
            try:
                event_index = event_id_shuffled.index(event_id)
            except:
                logging.warning('EventId %s is not in the templates of train data', event_id)
                #print('Warning: EventId %s is not in the templates of train data' %event_id)
                continue
            # Increase the feature/event/template count in event count matrix
            event_count_matrix[j, event_index] += 1
        # One label per instance. Labeling the instance if one log within is labeled at least
        labels.append(label)
    assert inst_number == len(labels)
    # Do not calc the num of instances that have anomalies on test dataset w/o validating
    if not ((para['train'] == False) and (para['extractLabel'] == False)):
        print("Among all instances, %d are anomalies"%sum(labels))
    #assert event_count_matrix.shape[0] == len(labels)

    np.savetxt(para['data_path']+'event_count_matrix.txt', event_count_matrix, fmt="%s")
    return event_count_matrix, labels
