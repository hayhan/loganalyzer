#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description : This file runs the predict models
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
import onnxruntime as rt

import featurextor
import weighting
import utils

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
#grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(parentdir)

logging.basicConfig(filename=parentdir+'/tmp/debug.log', \
                    format='%(asctime)s - %(message)s', \
                    level=logging.ERROR)

# Read some parameters from the config file
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    # Metrics enable
    metricsEn = bool(conlines[1].strip() == 'METRICS=1')

    # Read the model name
    if conlines[2].strip() == 'MODEL=DT':
        PRED_MODEL_FILE = 'DecesionTree.onnx'
        INC_UPDATE = False
    elif conlines[2].strip() == 'MODEL=LR':
        PRED_MODEL_FILE = 'LR.onnx'
        INC_UPDATE = False
    elif conlines[2].strip() == 'MODEL=SVM':
        PRED_MODEL_FILE = 'SVM.onnx'
        INC_UPDATE = False
    elif conlines[2].strip() == 'MODEL=RFC':
        PRED_MODEL_FILE = 'RandomForest.onnx'
        INC_UPDATE = False
    elif conlines[2].strip() == 'MODEL=MultinomialNB':
        PRED_MODEL_FILE = 'MultinomialNB.onnx'
        INC_UPDATE = True
    elif conlines[2].strip() == 'MODEL=Perceptron':
        PRED_MODEL_FILE = 'Perceptron.onnx'
        INC_UPDATE = True
    elif conlines[2].strip() == 'MODEL=SGDC_SVM':
        PRED_MODEL_FILE = 'SGDC_SVM.onnx'
        INC_UPDATE = True
    elif conlines[2].strip() == 'MODEL=SGDC_LR':
        PRED_MODEL_FILE = 'SGDC_LR.onnx'
        INC_UPDATE = True
    else:
        print("The model name is wrong. Exit.")
        sys.exit(1)

    # Read the sliding window size
    window_size = int(conlines[3].strip().replace('WINDOW_SIZE=', ''))
    # Read the sliding window step size
    window_step = int(conlines[4].strip().replace('WINDOW_STEP=', ''))

para_test = {
    'labels_file'    : parentdir+'/results/test/test_norm.txt_labels.csv',
    'structured_file': parentdir+'/results/test/test_norm.txt_structured.csv',
    'templates_file' : parentdir+'/results/test/test_norm.txt_templates.csv',
    'data_path'      : parentdir+'/results/test/',
    'persist_path'   : parentdir+'/results/persist/',
    'window_size'    : window_size,    # milliseconds
    'step_size'      : window_step,    # milliseconds
    'window_rebuild' : True,
    'train'          : False,
    'extractLabel'   : metricsEn,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}


if __name__ == '__main__':
    print("===> Predict Model: {}\n".format(PRED_MODEL_FILE))

    #####################################################################################
    # Feature extraction for the train data
    #####################################################################################

    # Load the test data from files and do some pre-processing
    raw_data_test, \
    event_mapping_data_test, \
    event_id_templates_test = featurextor.load_data(para_test)

    # Add sliding window and create the event count matrix for the test data set.
    # The input parameter event_id_templates_test is not used actually, we reuse
    # the saved shuffled EventId list in the training step.
    test_x, test_y = featurextor.add_sliding_window(para_test, raw_data_test, \
                                                    event_mapping_data_test, \
                                                    event_id_templates_test, \
                                                    feat_ext_inc=INC_UPDATE)

    # Add weighting factor as we did for training data
    test_x = weighting.transform(para_test, test_x, term_weighting='tf-idf', \
                                  use_train_factor=True, df_vec_inc=INC_UPDATE)

    # Load the ONNX model which is equivalent to the scikit-learn model
    # https://microsoft.github.io/onnxruntime/python/api_summary.html
    sess = rt.InferenceSession(para_test['persist_path']+PRED_MODEL_FILE)
    input_name = sess.get_inputs()[0].name
    label_name = sess.get_outputs()[0].name
    test_y_pred = sess.run([label_name], {input_name: test_x.astype(np.float32)})[0]

    #test_y_pred = model.predict(test_x)
    #np.savetxt(para_test['data_path']+'test_y_data.txt', test_y, fmt="%s")
    #np.savetxt(para_test['data_path']+'test_y_data_pred.txt', test_y_pred, fmt="%s")

    if metricsEn:
        print('Test validation:')
        precision, recall, f1 = utils.metrics(test_y_pred, test_y)
        print('Precision: {:.3f}, recall: {:.3f}, F1-measure: {:.3f}\n'\
              .format(precision, recall, f1))

    #####################################################################################
    # Trace anomaly timestamp windows in the raw log file, aka. loganalyzer/logs/test.txt
    #####################################################################################

    # Read window tuple list for test data
    sliding_window_file = para_test['data_path']+'sliding_'+str(para_test['window_size']) \
                          +'ms_'+str(para_test['step_size'])+'ms.csv'
    window_list = pd.read_csv(sliding_window_file, header=None).values

    anomaly_window_list = []
    for i, pred_result in enumerate(test_y_pred):
        if pred_result:
            start_index = window_list[i][0]
            end_index = window_list[i][1]
            anomaly_window_list.append(tuple((start_index, end_index)))
    logging.debug('The anomaly index tuples: {}'.format(anomaly_window_list))

    # Read test data from normalized / structured logs
    data_df = pd.read_csv(para_test['structured_file'], usecols=['Time'])
    #data_df['Time'] = pd.to_datetime(data_df['Time'], format="[%Y%m%d-%H:%M:%S.%f]")
    norm_time_list = data_df['Time'].to_list()

    anomaly_timestamp_list = []
    for _i, anomaly_window in enumerate(anomaly_window_list):
        x = anomaly_window[0]
        y = anomaly_window[1]
        anomaly_timestamp_list.append(tuple((norm_time_list[x], norm_time_list[y])))
    logging.debug('The anomaly timestamps: {}'.format(anomaly_timestamp_list))

    # Save the final timestamp tuples of anomaly
    np.savetxt(para_test['data_path']+'anomaly_timestamp.csv', anomaly_timestamp_list, \
               delimiter=',', fmt='%s')
