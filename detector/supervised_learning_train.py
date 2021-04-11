#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description : Train/validate different models
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import logging
import joblib
import numpy as np
import pandas as pd

from sklearn import tree
from sklearn import svm
from sklearn.naive_bayes import MultinomialNB
#from sklearn.linear_model import Perceptron
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

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

    # The log type
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')
    # Metrics enable
    metricsEn = bool(conlines[2].strip() == 'METRICS=1')

    # Read the model name
    if conlines[3].strip() == 'MODEL=DT':
        MODEL_NAME = 'DecesionTree'
        INC_UPDATE = False
    elif conlines[3].strip() == 'MODEL=LR':
        MODEL_NAME = 'LR'
        INC_UPDATE = False
    elif conlines[3].strip() == 'MODEL=SVM':
        MODEL_NAME = 'SVM'
        INC_UPDATE = False
    elif conlines[3].strip() == 'MODEL=RFC':
        MODEL_NAME = 'RandomForest'
        INC_UPDATE = False
    elif conlines[3].strip() == 'MODEL=MultinomialNB':
        MODEL_NAME = 'MultinomialNB'
        INC_UPDATE = True
    elif conlines[3].strip() == 'MODEL=Perceptron':
        MODEL_NAME = 'Perceptron'
        INC_UPDATE = True
    elif conlines[3].strip() == 'MODEL=SGDC_SVM':
        MODEL_NAME = 'SGDC_SVM'
        INC_UPDATE = True
    elif conlines[3].strip() == 'MODEL=SGDC_LR':
        MODEL_NAME = 'SGDC_LR'
        INC_UPDATE = True
    else:
        print("The model name is wrong. Exit.")
        sys.exit(1)

    # Read the sliding window size
    window_size = int(conlines[4].strip().replace('WINDOW_SIZE=', ''))
    # Read the sliding window step size
    window_step = int(conlines[5].strip().replace('WINDOW_STEP=', ''))
    # Read the template library size
    tmplib_size = int(conlines[6].strip().replace('TEMPLATE_LIB_SIZE=', ''))

# Abstract results directories
results_persist_dir = parentdir + '/results/persist/' + LOG_TYPE + '/'
results_train_dir = parentdir + '/results/train/' + LOG_TYPE + '/'
results_test_dir = parentdir + '/results/test/' + LOG_TYPE + '/'

para_train = {
    'labels_file'    : results_train_dir+'train_norm.txt_labels.csv',
    'structured_file': results_train_dir+'train_norm.txt_structured.csv',
    'templates_file' : results_train_dir+'train_norm.txt_templates.csv',
    'data_path'      : results_train_dir,
    'persist_path'   : results_persist_dir,
    'window_size'    : window_size,    # milliseconds
    'step_size'      : window_step,    # milliseconds
    'tmplib_size'    : tmplib_size,    # only for train dataset
    'window_rebuild' : True,
    'train'          : True,
    'extractLabel'   : metricsEn,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}

para_test = {
    'labels_file'    : results_test_dir+'test_norm.txt_labels.csv',
    'structured_file': results_test_dir+'test_norm.txt_structured.csv',
    'templates_file' : results_test_dir+'test_norm.txt_templates.csv',
    'data_path'      : results_test_dir,
    'persist_path'   : results_persist_dir,
    'window_size'    : window_size,    # milliseconds
    'step_size'      : window_step,    # milliseconds
    'window_rebuild' : True,
    'train'          : False,
    'extractLabel'   : metricsEn,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}


if __name__ == '__main__':
    print("===> Train Model: {}\n".format(MODEL_NAME))

    #####################################################################################
    # Feature extraction for the train data
    #####################################################################################

    # Load the train data from files and do some pre-processing
    raw_data_train, \
    event_mapping_data_train, \
    event_id_templates_train = featurextor.load_data(para_train, feat_ext_inc=INC_UPDATE)

    # Add sliding window and create the event count matrix for the train data set
    # All the EventId in templates are shuffed and saved under results folder
    train_x, train_y = featurextor.add_sliding_window(para_train, raw_data_train, \
                                                      event_mapping_data_train, \
                                                      event_id_templates_train, \
                                                      feat_ext_inc=INC_UPDATE)

    # Add weighting factor before training
    train_x = weighting.fit_transform(para_train, train_x, term_weighting='tf-idf', \
                                      df_vec_inc=INC_UPDATE)

    #####################################################################################
    # Train the model with train dataset now
    #####################################################################################

    # Load the saved complete scikit-learn model if it exists
    inc_fit_model_file = para_train['persist_path']+MODEL_NAME+'.object'
    all_classes = np.array([0, 1])

    # Incremental training at the 1st time
    if INC_UPDATE and not os.path.exists(inc_fit_model_file):
        if MODEL_NAME == 'MultinomialNB':
            model = MultinomialNB(alpha=1.0, fit_prior=True, class_prior=None)
        elif MODEL_NAME == 'Perceptron':
            model = SGDClassifier(loss='perceptron', max_iter=1000)
        elif MODEL_NAME == 'SGDC_SVM':
            model = SGDClassifier(loss='hinge', max_iter=1000)
        else:
            # SGDC_LR
            model = SGDClassifier(loss='log', max_iter=1000)
        print("First time training...: {}\n".format(MODEL_NAME))
    # Incremental training ...
    elif INC_UPDATE:
        model = joblib.load(inc_fit_model_file)
        print("Incremental training...: {}\n".format(MODEL_NAME))
    # Normal training ...
    else:
        if MODEL_NAME == 'DecesionTree':
            model = tree.DecisionTreeClassifier(criterion='gini', max_depth=None, \
                            max_features=None, class_weight=None)
        elif MODEL_NAME == 'LR':
            model = LogisticRegression(penalty='l2', C=100, tol=0.01, \
                            class_weight=None, solver='liblinear', max_iter=100)
        elif MODEL_NAME == 'SVM':
            model = svm.LinearSVC(penalty='l1', tol=0.1, C=1, dual=False, \
                            class_weight=None, max_iter=100)
        else:
            # Random Forest Classifier
            model = RandomForestClassifier(n_estimators=100)
        print("Normal training...: {}\n".format(MODEL_NAME))

    if INC_UPDATE:
        #model.fit(train_x, train_y)
        model.partial_fit(train_x, train_y, classes=all_classes)
        # Save the model object for incremental learning
        joblib.dump(model, inc_fit_model_file)
    else:
        model.fit(train_x, train_y)

    # Persist the model for deployment by using sklearn-onnx converter
    # http://onnx.ai/sklearn-onnx/
    initial_type = [('float_input', FloatTensorType([None, train_x.shape[1]]))]
    onx = convert_sklearn(model, initial_types=initial_type)
    with open(para_train['persist_path']+MODEL_NAME+'.onnx', "wb") as f:
        f.write(onx.SerializeToString())

    # Predict the train data for validation later
    train_y_pred = model.predict(train_x)

    #####################################################################################
    # Feature extraction for the test data
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
    test_x  = weighting.transform(para_test, test_x, term_weighting='tf-idf', \
                                  use_train_factor=True, df_vec_inc=INC_UPDATE)

    test_y_pred = model.predict(test_x)
    #np.savetxt(para_test['data_path']+'test_y_data.txt', test_y, fmt="%s")
    np.savetxt(para_test['data_path']+'test_y_data_pred.txt', test_y_pred, fmt="%s")

    #####################################################################################
    # The validation for train and test dataset
    #####################################################################################

    print('Train validation:')
    precision, recall, f1 = utils.metrics(train_y_pred, train_y)
    print('Precision: {:.3f}, recall: {:.3f}, F1-measure: {:.3f}\n'\
          .format(precision, recall, f1))

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
