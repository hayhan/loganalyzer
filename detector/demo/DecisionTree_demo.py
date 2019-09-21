#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pickle
import logging
import numpy as np
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(grandpadir)

from sklearn import tree
from detector import featurextor, weighting, utils
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

logging.basicConfig(filename=grandpadir+'/tmp/debug.log', \
                    format='%(asctime)s - %(message)s', \
                    level=logging.ERROR)

# Read some parameters from the config file
with open(grandpadir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    # Read the sliding window size
    window_size = int(conlines[2].strip().replace('WINDOW_SIZE=', ''))
    # Read the sliding window step size
    window_step = int(conlines[3].strip().replace('WINDOW_STEP=', ''))

para_train = {
    'labeled_file'   : grandpadir+'/results/train/train_norm.txt_labeled.csv',
    'structured_file': grandpadir+'/results/train/train_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/train/train_norm.txt_templates.csv',
    'data_path'      : grandpadir+'/results/train/',
    'persist_path'   : grandpadir+'/results/persist/',
    'window_size'    : window_size,    # milliseconds
    'step_size'      : window_step,    # milliseconds
    'window_rebuild' : False,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}

para_test = {
    'labeled_file'   : grandpadir+'/results/test/test_norm.txt_labeled.csv',
    'structured_file': grandpadir+'/results/test/test_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/test/test_norm.txt_templates.csv',
    'data_path'      : grandpadir+'/results/test/',
    'persist_path'   : grandpadir+'/results/persist/',
    'window_size'    : window_size,    # milliseconds
    'step_size'      : window_step,    # milliseconds
    'window_rebuild' : True,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}


if __name__ == '__main__':
    """
    Feature extraction for the train data
    """
    # Load the train data from files and do some pre-processing
    raw_data_train, \
    event_mapping_data_train, \
    event_id_templates_train = featurextor.load_DOCSIS(para_train)

    # Add sliding window and create the event count matrix for the train data set
    # All the EventId in templates are shuffed and saved under results folder
    train_x, train_y = featurextor.add_sliding_window(para_train, raw_data_train, \
                                                      event_mapping_data_train, \
                                                      event_id_templates_train)

    """
    # This part code is not used any more after we de-coupled the train and test data set
    # Split event_count_matrix into train and test data sets
    num_train = int(para['train_ratio'] * len(labels))
    train_x = event_count_matrix[0:num_train]
    train_y = labels[0:num_train]
    print('there are %d instances in train dataset,'% len(train_y), '%d are anomalies'%sum(train_y))

    test_x = event_count_matrix[num_train:]
    test_y = labels[num_train:]
    print('there are %d instances in test dataset,'% len(test_y), '%d are anomalies'%sum(test_y))
    """

    # Add weighting factor before training
    train_x = weighting.fit_transform(para_train, train_x, term_weighting='tf-idf')

    """
    # Do not need this because I removed the weighting class
    # Save the weighting object in training to disk for future predict
    with open(para_train['persist_path']+'weighting.object', 'wb') as f:
        pickle.dump(weighting_class, f)
    """

    """
    Train the model with train dataset now
    """
    model = tree.DecisionTreeClassifier(criterion='gini', max_depth=None, \
                                        max_features=None, class_weight=None)
    model.fit(train_x, train_y)

    # Save the model object after training to disk for future predict
    """
    with open(para_train['persist_path']+'DecisionTree.object', 'wb') as f:
        pickle.dump(model, f)
    """
    # Persist the model for deployment by using sklearn-onnx converts instead
    # http://onnx.ai/sklearn-onnx/
    initial_type = [('float_input', FloatTensorType([None, train_x.shape[1]]))]
    onx = convert_sklearn(model, initial_types=initial_type)
    with open(para_train['persist_path']+"DecesionTree.onnx", "wb") as f:
        f.write(onx.SerializeToString())

    # Predict the train data for validation later
    train_y_pred = model.predict(train_x)

    """
    Feature extraction for the test data
    """
    # Load the test data from files and do some pre-processing
    raw_data_test, \
    event_mapping_data_test, \
    event_id_templates_test = featurextor.load_DOCSIS(para_test)
    
    # Add sliding window and create the event count matrix for the test data set.
    # The input parameter event_id_templates_test is not used actually, we reuse
    # the saved shuffled EventId list in the training step.
    test_x, test_y = featurextor.add_sliding_window(para_test, raw_data_test, \
                                                    event_mapping_data_test, \
                                                    event_id_templates_test)

    # Add weighting factor as we did for training data
    test_x  = weighting.transform(para_test, test_x, term_weighting='tf-idf', use_train_factor=True)

    test_y_pred = model.predict(test_x)
    #np.savetxt(para_test['data_path']+'test_y_data.txt', test_y, fmt="%s")
    np.savetxt(para_test['data_path']+'test_y_data_pred.txt', test_y_pred, fmt="%s")

    """
    The validation for train and test dataset
    """
    print('Train validation:')
    precision, recall, f1 = utils.metrics(train_y_pred, train_y)
    print('Precision: {:.3f}, recall: {:.3f}, F1-measure: {:.3f}\n'.format(precision, recall, f1))

    print('Test validation:')
    precision, recall, f1 = utils.metrics(test_y_pred, test_y)
    print('Precision: {:.3f}, recall: {:.3f}, F1-measure: {:.3f}\n'.format(precision, recall, f1))

    """
    Trace anomaly timestamp windows in the raw log file, aka. loganalyzer/logs/test.txt
    """
    # Read window tuple list for test data
    sliding_window_file = para_test['data_path']+'sliding_'+str(para_test['window_size']) \
                          +'ms_'+str(para_test['step_size'])+'ms.csv'
    window_list = pd.read_csv(sliding_window_file, header=None).values

    anomaly_window_list = []
    for i in range(len(test_y_pred)):
        if test_y_pred[i]:
            start_index = window_list[i][0]
            end_index = window_list[i][1]
            anomaly_window_list.append(tuple((start_index, end_index)))
    logging.debug('The anomaly index tuples: {}'.format(anomaly_window_list))

    # Read test data from normalized / structured logs
    data_df = pd.read_csv(para_test['structured_file'], usecols=['Time'])
    #data_df['Time'] = pd.to_datetime(data_df['Time'], format="[%Y%m%d-%H:%M:%S.%f]")
    norm_time_list = data_df['Time'].to_list()

    anomaly_timestamp_list = []
    for i in range(len(anomaly_window_list)):
        x = anomaly_window_list[i][0]
        y = anomaly_window_list[i][1]
        anomaly_timestamp_list.append(tuple((norm_time_list[x], norm_time_list[y])))
    logging.debug('The anomaly timestamps: {}'.format(anomaly_timestamp_list))

    # Save the final timestamp tuples of anomaly
    np.savetxt(para_test['data_path']+'anomaly_timestamp.csv', anomaly_timestamp_list, delimiter=',',fmt='%s')