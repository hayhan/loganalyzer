#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import pickle
import logging
import numpy as np
import pandas as pd
import onnxruntime as rt

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(grandpadir)

from detector import featurextor, weighting, utils

logging.basicConfig(filename=grandpadir+'/tmp/debug.log', \
                    format='%(asctime)s - %(message)s', \
                    level=logging.ERROR)

# Read some parameters from the config file
with open(grandpadir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    if conlines[1].strip() == 'MODEL=DT':
        model_file = 'DecesionTree.onnx'
    elif conlines[1].strip() == 'MODEL=LR':
        model_file = 'LR.onnx'
    else:
        model_file = 'SVM.onnx'



para_test = {
    'labeled_file'   : grandpadir+'/results/test/test_norm.txt_labeled.csv',
    'structured_file': grandpadir+'/results/test/test_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/test/test_norm.txt_templates.csv',
    'data_path'      : grandpadir+'/results/test/',
    'persist_path'   : grandpadir+'/results/persist/',
    'window_size'    : 10000,    # milliseconds
    'step_size'      : 5000,     # milliseconds
    'window_rebuild' : True,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}

if __name__ == '__main__':
    """
    Feature extraction for the test data
    """
    """
    # Load the objects we saved in training
    # The weighting object from training
    with open(para_test['persist_path']+'weighting.object', 'rb') as f:
        weighting_class = pickle.load(f)
    """
    
    """
    # The model object from training
    with open(para_test['persist_path']+'DecisionTree.object', 'rb') as f:
    #with open(para_test['persist_path']+'LR.object', 'rb') as f:
    #with open(para_test['persist_path']+'SVM.object', 'rb') as f:
        model = pickle.load(f)
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

    # Load the ONNX model which is equivalent to the scikit-learn model
    # https://microsoft.github.io/onnxruntime/api_summary.html
    sess = rt.InferenceSession(para_test['persist_path']+model_file)
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    test_y_pred = sess.run([label_name], {input_name: test_x.astype(np.float32)})[0]

    #test_y_pred = model.predict(test_x)
    #np.savetxt(para_test['data_path']+'test_y_data.txt', test_y, fmt="%s")
    #np.savetxt(para_test['data_path']+'test_y_data_pred.txt', test_y_pred, fmt="%s")

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