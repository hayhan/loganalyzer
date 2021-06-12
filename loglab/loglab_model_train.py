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
from sklearn import utils
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import KFold
from sklearn.model_selection import cross_val_score
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType


# import matplotlib.pyplot as plt

KFOLD_MANU = False
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
        MODEL_NAME = 'RandomForest'
    else:
        print("The model name is wrong. Exit.")
        sys.exit(1)

    # Read the sliding window size
    WINDOW_SIZE = int(conlines[4].strip().replace('WINDOW_SIZE=', ''))
    # Read the template library size
    TMPLIB_SIZE = int(conlines[6].strip().replace('TEMPLATE_LIB_SIZE=', ''))

# Abstract results directories
results_persist_dir = parentdir + '/results/persist/' + LOG_TYPE + '/'
results_train_dir = parentdir + '/results/train/' + LOG_TYPE + '/'
results_test_dir = parentdir + '/results/test/' + LOG_TYPE + '/'

para_train = {
    'structured_file': results_train_dir+'train_norm.txt_structured.csv',
    'saminfo_file'   : results_train_dir+'train_norm.txt_saminfo.pkl',
    'template_lib'   : results_persist_dir+'template_lib.csv',
    'eid_file'       : results_persist_dir+'event_id_loglab.npy',
    'eid_file_txt'   : results_persist_dir+'event_id_loglab.txt',
    'data_path'      : results_train_dir,
    'persist_path'   : results_persist_dir,
    'window_size'    : WINDOW_SIZE,    # unit is log
    'tmplib_size'    : TMPLIB_SIZE,
    'train'          : True,
    'metrics_enable' : METRICS_EN,
    'weight'         : 2,
}

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
    print("===> Train Loglab Model: {}\n".format(MODEL_NAME))

    #------------------------------------------------------------------------------------
    # Load data and do feature extraction on the training dataset
    #------------------------------------------------------------------------------------

    # x_train data type is float while y_train is integer here
    x_train, y_train = dload.load_data(para_train)

    # Save the event count matrix
    # np.savetxt(para_train['data_path']+'loglab_event_count_matrix.txt', x_train, fmt="%s")

    # Visualize the sparse matrix
    # plt.spy(x_train, markersize=1)
    # plt.show()

    # Feature scaling
    # TBD:
    # scaler = StandardScaler()
    # x_train = scaler.fit_transform(x_train)

    #------------------------------------------------------------------------------------
    # Select models and tune the parameters by cross validation
    #------------------------------------------------------------------------------------
    if MODEL_NAME == 'RandomForest':
        model = RandomForestClassifier(n_estimators=100)
    else:
        print("The model name is not defined. Exit.")
        sys.exit(1)

    #------------------------------------------------------------------------------------
    # k-fold cross validation
    # We can use numpy, pandas or sklearn KFold api directly.
    #------------------------------------------------------------------------------------

    # Convert the class target list to column array and merge with x_train
    class_vec = np.reshape(y_train, (len(y_train), 1))
    # The monolith dataset is type of float including the last column, which is class labels
    monolith_data = np.hstack((x_train, class_vec))

    # Randomize the training samples
    monolith_data = utils.shuffle(monolith_data)
    # print(f"monolith_data:\n{monolith_data}\nlen of monolith_data:{(monolith_data).shape}")

    if KFOLD_MANU:
        # Leave-one-out cross validation
        k = len(y_train)
        k_sample_count = monolith_data.shape[0] // k

        for fold in range(k):
            test_begin = k_sample_count * fold
            test_end = k_sample_count * (fold + 1)

            test_data = monolith_data[test_begin: test_end]

            train_data = np.vstack([
                monolith_data[:test_begin],
                monolith_data[test_end:]
            ])

            # Train the model with train data
            x_train = train_data[:, :-1]
            y_train = train_data[:, -1].astype(int)
            model.fit(x_train, y_train)

            # Validate the model with test data
            x_test = test_data[:, :-1]
            y_test = test_data[:, -1].astype(int)
            y_test_pred = model.predict(x_test)
            print(y_test, y_test_pred)

    else:
        # Initialise the number of folds k for doing CV
        kfold = KFold(n_splits=66)
        x_train = monolith_data[:, :-1]
        y_train = monolith_data[:, -1].astype(int)

        # Evaluate the model using k-fold CV
        scores = cross_val_score(model, x_train, y_train, cv=kfold, scoring='accuracy')

        # Get the model performance metrics
        print(scores)
        print("Mean: " + str(scores.mean()))

    #------------------------------------------------------------------------------------
    # Train model with the optimized parameters in validation or models and distrubute it
    #------------------------------------------------------------------------------------
    x_train = monolith_data[:, :-1]
    y_train = monolith_data[:, -1].astype(int)
    model.fit(x_train, y_train)

    # Persist the model for deployment by using sklearn-onnx converter
    # http://onnx.ai/sklearn-onnx/
    initial_type = [('float_input', FloatTensorType([None, x_train.shape[1]]))]
    onx = convert_sklearn(model, initial_types=initial_type)
    with open(para_train['persist_path']+'loglab_'+MODEL_NAME+'.onnx', "wb") as f:
        f.write(onx.SerializeToString())
