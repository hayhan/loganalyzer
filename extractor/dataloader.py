"""
The interface to load log datasets. The datasets currently supported include
HDFS and BGL.

Authors:
    LogPAI Team

"""

import pandas as pd
import os
import numpy as np
import re
import sys
from sklearn.utils import shuffle
from collections import OrderedDict
from collections import Counter

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

def load_DOCSIS():
    """  Load DOCSIS normalized / structured logs into train and test data

    Arguments
    ---------
    para: the parameters dictionary

    Returns
    -------
    raw_data: list of (label, time)
    event_mapping_data: a list of event index, where each row index indicates a corresponding log
    """

    # Read labeled info
    data_df1 = pd.read_csv(parentdir+'/results/test_norm.txt_labeled.csv', usecols=['Label'])
    data_df1['Label'] = (data_df1['Label'] != '-').astype(int)

    # Read data from normolized / structured logs
    data_df2 = pd.read_csv(parentdir+'/results/test_norm.txt_structured.csv', usecols=['Time', 'EventId'])
    data_df2['Time'] = pd.to_datetime(data_df2['Time'], format="[%Y%m%d-%H:%M:%S.%f]")
    # Convert timestamp to millisecond unit
    data_df2['Ms_Elapsed'] = ((data_df2['Time']-data_df2['Time'][0]).dt.total_seconds()*1000).astype(int)

    data_df2['Label'] = data_df1['Label']
    raw_data = data_df2[['Label','Ms_Elapsed']].values

    event_mapping_data = data_df2['EventId'].values

    #print(type(data_df2))
    #print(raw_data)
    #print(event_mapping_data)
    print('The number of anomaly logs is %d, but it requires further processing' % sum(raw_data[:, 0]))
    return raw_data, event_mapping_data


def add_sliding_window(raw_data, event_mapping_data):
    """ split logs into sliding windows, built an event count matrix and get the corresponding label

    Args:
    --------
    para: the parameters dictionary
    raw_data: list of (label, time)
    event_mapping_data: a list of event index, where each row index indicates a corresponding log

    Returns:
    --------
    event_count_matrix: event count matrix, where each row is an instance (log sequence vector)
    labels: a list of labels, 1 represents anomaly
    """

    # create the directory for saving the sliding windows (start_index, end_index), which can be directly loaded in future running
    if not os.path.exists(parentdir+'/results/windows'):
        os.mkdir(parentdir+'/results/windows')
"""
    log_size = raw_data.shape[0]
    sliding_file_path = para['save_path']+'sliding_'+str(para['window_size'])+'h_'+str(para['step_size'])+'h.csv'

    #=============divide into sliding windows=========#
    start_end_index_list = [] # list of tuples, tuple contains two number, which represent the start and end of sliding time window
    label_data, time_data = raw_data[:,0], raw_data[:, 1]
    if not os.path.exists(sliding_file_path):
        # split into sliding window
        start_time = time_data[0]
        start_index = 0
        end_index = 0

        # get the first start, end index, end time
        for cur_time in time_data:
            if  cur_time < start_time + para['window_size']*3600:
                end_index += 1
                end_time = cur_time
            else:
                start_end_pair=tuple((start_index,end_index))
                start_end_index_list.append(start_end_pair)
                break
        # move the start and end index until next sliding window
        while end_index < log_size:
            start_time = start_time + para['step_size']*3600
            end_time = end_time + para['step_size']*3600
            for i in range(start_index,end_index):
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
        inst_number = len(start_end_index_list)
        print('there are %d instances (sliding windows) in this dataset\n'%inst_number)
        np.savetxt(sliding_file_path,start_end_index_list,delimiter=',',fmt='%d')
    else:
        print('Loading start_end_index_list from file')
        start_end_index_list = pd.read_csv(sliding_file_path, header=None).values
        inst_number = len(start_end_index_list)
        print('there are %d instances (sliding windows) in this dataset' % inst_number)

    # get all the log indexes in each time window by ranging from start_index to end_index
    expanded_indexes_list=[]
    for t in range(inst_number):
        index_list = []
        expanded_indexes_list.append(index_list)
    for i in range(inst_number):
        start_index = start_end_index_list[i][0]
        end_index = start_end_index_list[i][1]
        for l in range(start_index, end_index):
            expanded_indexes_list[i].append(l)

    event_mapping_data = [row[0] for row in event_mapping_data]
    event_num = len(list(set(event_mapping_data)))
    print('There are %d log events'%event_num)

    #=============get labels and event count of each sliding window =========#
    labels = []
    event_count_matrix = np.zeros((inst_number,event_num))
    for j in range(inst_number):
        label = 0   #0 represent success, 1 represent failure
        for k in expanded_indexes_list[j]:
            event_index = event_mapping_data[k]
            event_count_matrix[j, event_index] += 1
            if label_data[k]:
                label = 1
                continue
        labels.append(label)
    assert inst_number == len(labels)
    print("Among all instances, %d are anomalies"%sum(labels))
    assert event_count_matrix.shape[0] == len(labels)
    return event_count_matrix, labels
"""