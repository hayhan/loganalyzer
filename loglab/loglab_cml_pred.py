#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description : Train/validate different models for Loglab multi-classification
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import logging
import joblib
import numpy as np
import pandas as pd
import loglab_data_load as dload
import onnxruntime as rt
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_recall_fscore_support


curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
sys.path.append(parentdir)

logging.basicConfig(filename=parentdir+'/tmp/debug.log', \
                    format='%(asctime)s - %(message)s', \
                    level=logging.ERROR)

# Read some parameters from the config file
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    # The log type
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')
    # Metrics enable
    METRICS_EN = bool(conlines[2].strip() == 'METRICS=1')

    # Read the model name
    if conlines[3].strip() == 'MODEL=LOGLAB.RFC':
        PRED_MODEL_FILE = 'loglab_RandomForest.onnx'
    else:
        print("The model name is wrong. Exit.")
        sys.exit(1)

    # Read the sliding window size
    WINDOW_SIZE = int(conlines[4].strip().replace('WINDOW_SIZE=', ''))
    # Read the template library size
    TMPLIB_SIZE = int(conlines[6].strip().replace('TEMPLATE_LIB_SIZE=', ''))

# Abstract results directories
results_persist_dir = parentdir + '/results/persist/' + LOG_TYPE + '/'
results_test_dir = parentdir + '/results/test/' + LOG_TYPE + '/'

para_test = {
    'structured_file': results_test_dir+'test_norm.txt_structured.csv',
    'saminfo_file'   : results_test_dir+'test_norm.txt_saminfo.pkl',
    'template_lib'   : results_persist_dir+'template_lib.csv',
    'eid_file'       : results_persist_dir+'event_id_loglab.npy',
    'eid_file_txt'   : results_persist_dir+'event_id_loglab.txt',
    'data_path'      : results_test_dir,
    'persist_path'   : results_persist_dir,
    'window_size'    : WINDOW_SIZE,    # unit is log
    'tmplib_size'    : TMPLIB_SIZE,
    'train'          : False,
    'metrics_enable' : METRICS_EN,
    'weight'         : 2,
}


if __name__ == '__main__':
    print("===> Predict With Loglab Model: {}\n".format(PRED_MODEL_FILE))

    #------------------------------------------------------------------------------------
    # Load data and do feature extraction on the test dataset
    #------------------------------------------------------------------------------------
    x_test, _ = dload.load_data(para_test)

    # Feature scaling based on training dataset
    # TBD:
    # scaler = StandardScaler()
    # x_test = scaler.transform(x_test)

    # Load the ONNX model which is equivalent to the scikit-learn model
    # https://microsoft.github.io/onnxruntime/python/api_summary.html
    sess = rt.InferenceSession(para_test['persist_path']+PRED_MODEL_FILE)
    input_name = sess.get_inputs()[0].name

    # Target class
    label_name = sess.get_outputs()[0].name
    y_pred = sess.run([label_name], {input_name: x_test.astype(np.float32)})[0]
    print(y_pred)

    # Probability of each target class
    label_name = sess.get_outputs()[1].name
    y_pred_prob = sess.run([label_name], {input_name: x_test.astype(np.float32)})[0]
    print(y_pred_prob)