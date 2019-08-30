"""
Description : To do feature extractor and create event count matrix
Author      : LogPAI Team, modified by Wei Han <wei.han@broadcom.com>
License     : MIT
"""
import logging
import pandas as pd
import os
import numpy as np
import re
import sys
from sklearn.utils import shuffle
#from collections import OrderedDict
#from collections import Counter

#curfiledir = os.path.dirname(__file__)
#parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))


def load_DOCSIS(para):
    """  Load DOCSIS normalized / structured logs into train and test data

    Arguments
    ---------
    para: the parameters dictionary

    Returns
    -------
    raw_data: list of (label, time)
    event_mapping_data: a list of event id mapping to each line (log)
    event_id_templates: a list mapping event id to index, e.g. -> 0, 1, ... in templates file
    """

    # Read labeled info
    data_df1 = pd.read_csv(para['labeled_file'], usecols=['Label'])
    data_df1['Label'] = (data_df1['Label'] != '-').astype(int)

    # Read data from normalized / structured logs
    data_df2 = pd.read_csv(para['structured_file'], usecols=['Time', 'EventId'])
    data_df2['Time'] = pd.to_datetime(data_df2['Time'], format="[%Y%m%d-%H:%M:%S.%f]")
    # Convert timestamp to millisecond unit
    data_df2['Ms_Elapsed'] = ((data_df2['Time']-data_df2['Time'][0]).dt.total_seconds()*1000).astype(int)

    data_df2['Label'] = data_df1['Label']
    raw_data = data_df2[['Label','Ms_Elapsed']].values

    event_mapping_data = data_df2['EventId'].values

    # Read EventId from templates file
    data_df3 = pd.read_csv(para['templates_file'], usecols=['EventId'])
    event_id_templates = data_df3['EventId'].to_list()

    #logging.debug(raw_data)
    #logging.debug(event_mapping_data)
    #logging.debug(event_id_templates)

    print('The number of anomaly logs is %d, but it requires further processing' % sum(raw_data[:, 0]))
    return raw_data, event_mapping_data, event_id_templates


def add_sliding_window(para, raw_data, event_mapping_data, event_id_templates):
    """ split logs into sliding windows, built an event count matrix and get the corresponding label

    Args:
    --------
    para: the parameters dictionary
    raw_data: list of (label, time)
    event_mapping_data: a list of event id mapping to each line (log)
    event_id_templates: a list mapping event id to index, e.g. -> 0, 1, ... in templates file

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
    event_id_shuffled_file = para['eventid_shuf']+'event_id_shuffled.npy'

    # Shuffle the event_id_templates
    if not os.path.exists(event_id_shuffled_file):
        event_id_shuffled = shuffle(event_id_templates)
        np.save(event_id_shuffled_file, event_id_shuffled)
    else:
        print('Loading shuffled EventId list in templates')
        event_id_shuffled = np.load(event_id_shuffled_file).tolist()
    #print(event_id_shuffled)

    #=============divide into sliding windows=========#
    start_end_index_list = [] # list of tuples, tuple contains two numbers, which represents the start and end of sliding window
    label_data, time_data = raw_data[:, 0], raw_data[:, 1]
    if not os.path.exists(sliding_window_file):
        # split into sliding windows
        start_time = time_data[0]
        start_index = 0
        end_index = -1

        # get the first start, end index, end time
        for cur_time in time_data:
            # Window end (end_time) selects the min if not equal
            if  cur_time <= start_time + para['window_size']:
                end_index += 1
                #end_time = cur_time
            else:
                start_end_pair=tuple((start_index, end_index))
                start_end_index_list.append(start_end_pair)
                break

        # move the start and end index until next sliding window
        # ToDo: time consuming here and need optimize the algorithm
        while end_index < log_size - 1:

            start_index = 0
            end_index = -1

            for cur_time in time_data:
                # Window start (start_time) selects the max if not equal
                if cur_time < start_time + para['step_size']:
                    start_index += 1
                else:
                    start_time = cur_time
                    break

            for cur_time in time_data:
                # Window end (end_time) selects the min if not equal
                if cur_time <= start_time + para['window_size']:
                    end_index += 1
                    #end_time = cur_time
                else:
                    break

            start_end_pair=tuple((start_index, end_index))
            start_end_index_list.append(start_end_pair)
            #print(start_end_index_list)

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
        print('there are %d instances (sliding windows) in this dataset\n'%inst_number)

        np.savetxt(sliding_window_file, start_end_index_list, delimiter=',',fmt='%d')
    else:
        print('Loading start_end_index_list from file')
        start_end_index_list = pd.read_csv(sliding_window_file, header=None).values
        inst_number = len(start_end_index_list)
        print('there are %d instances (sliding windows) in this dataset' % inst_number)

    # get all the log indexes in each time window by ranging from start_index to end_index
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

    #=============get labels and event count of each sliding window =========#
    labels = []
    event_count_matrix = np.zeros((inst_number,len(event_id_shuffled)))
    for j in range(inst_number):
        label = 0   # 0 represent success, 1 represent failure
        for k in expanded_indexes_list[j]:
            event_id = event_mapping_data[k]
            # Convert EventId to ZERO based index
            try:
                event_index = event_id_shuffled.index(event_id)
            except:
                logging.warning('EventId %s is not in the templates of train data', event_id)
                #print('Warning: EventId %s is not in the templates of train data' %event_id)
                continue

            event_count_matrix[j, event_index] += 1
            if label_data[k]:
                label = 1
                continue
        labels.append(label)
    assert inst_number == len(labels)
    print("Among all instances, %d are anomalies"%sum(labels))
    assert event_count_matrix.shape[0] == len(labels)

    np.savetxt(para['data_path']+'event_count_matrix.txt', event_count_matrix, fmt="%s")
    return event_count_matrix, labels