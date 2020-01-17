#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Description : Train/validate different models
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import joblib
import logging
import numpy as np
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(grandpadir)

from sklearn import tree
from sklearn import svm
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import Perceptron
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import LogisticRegression

from detector import featurextor, weighting, utils
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType

logging.basicConfig(filename=grandpadir+'/tmp/debug.log', \
                    format='%(asctime)s - %(message)s', \
                    level=logging.ERROR)

# Read some parameters from the config file
with open(grandpadir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    # Read the model name
    if conlines[1].strip() == 'MODEL=DT':
        model_name = 'DecesionTree'
        incUpdate = False
    elif conlines[1].strip() == 'MODEL=LR':
        model_name = 'LR'
        incUpdate = False
    elif conlines[1].strip() == 'MODEL=SVM':
        model_name = 'SVM'
        incUpdate = False
    elif conlines[1].strip() == 'MODEL=MultinomialNB':
        model_name = 'MultinomialNB'
        incUpdate = True
    elif conlines[1].strip() == 'MODEL=Perceptron':
        model_name = 'Perceptron'
        incUpdate = True
    elif conlines[1].strip() == 'MODEL=SGDC_SVM':
        model_name = 'SGDC_SVM'
        incUpdate = True
    elif conlines[1].strip() == 'MODEL=SGDC_LR':
        model_name = 'SGDC_LR'
        incUpdate = True
    else:
        print("The incremental learning model name is wrong. Exit.")
        sys.exit(1)

    # Read the sliding window size
    window_size = int(conlines[2].strip().replace('WINDOW_SIZE=', ''))
    # Read the sliding window step size
    window_step = int(conlines[3].strip().replace('WINDOW_STEP=', ''))
    # Read the template library size
    tmplib_size = int(conlines[4].strip().replace('TEMPLATE_LIB_SIZE=', ''))

para_train = {
    'labels_file'   : grandpadir+'/results/train/train_norm.txt_labels.csv',
    'structured_file': grandpadir+'/results/train/train_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/train/train_norm.txt_templates.csv',
    'data_path'      : grandpadir+'/results/train/',
    'persist_path'   : grandpadir+'/results/persist/',
    'window_size'    : window_size,    # milliseconds
    'step_size'      : window_step,    # milliseconds
    'tmplib_size'    : tmplib_size,    # only for train dataset
    'window_rebuild' : True,
    'train'          : True,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}

para_test = {
    'labels_file'   : grandpadir+'/results/test/test_norm.txt_labels.csv',
    'structured_file': grandpadir+'/results/test/test_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/test/test_norm.txt_templates.csv',
    'data_path'      : grandpadir+'/results/test/',
    'persist_path'   : grandpadir+'/results/persist/',
    'window_size'    : window_size,    # milliseconds
    'step_size'      : window_step,    # milliseconds
    'window_rebuild' : True,
    'train'          : False,
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}


if __name__ == '__main__':
    print("===> Train Module: {}\n".format(model_name))

    """
    Feature extraction for the train data
    """
    # Load the train data from files and do some pre-processing
    raw_data_train, \
    event_mapping_data_train, \
    event_id_templates_train = featurextor.load_DOCSIS(para_train, feat_ext_inc=incUpdate)

    # Add sliding window and create the event count matrix for the train data set
    # All the EventId in templates are shuffed and saved under results folder
    train_x, train_y = featurextor.add_sliding_window(para_train, raw_data_train, \
                                                      event_mapping_data_train, \
                                                      event_id_templates_train, \
                                                      feat_ext_inc=incUpdate)

    # Add weighting factor before training
    train_x = weighting.fit_transform(para_train, train_x, term_weighting='tf-idf', df_vec_inc=incUpdate)

    """
    Train the model with train dataset now
    """
    # Load the saved complete scikit-learn model if it exists
    inc_fit_model_file = para_train['persist_path']+model_name+'.object'
    all_classes = np.array([0, 1])

    # Incremental training at the 1st time
    if incUpdate and not os.path.exists(inc_fit_model_file):
        if model_name == 'MultinomialNB':
            model = MultinomialNB(alpha=1.0, fit_prior=True, class_prior=None)
        elif model_name == 'Perceptron':
            model = Perceptron()
        elif model_name == 'SGDC_SVM':
            model = SGDClassifier(loss='hinge', max_iter=1000)
        else:
            # SGDC_LR
            model = SGDClassifier(loss='log', max_iter=1000)
        print("First time training...: {}\n".format(model_name))
    # Incremental training ...
    elif incUpdate:
        model = joblib.load(inc_fit_model_file)
        print("Incremental training...: {}\n".format(model_name))
    # Normal training ...
    else:
        if model_name == 'DecesionTree':
            model = tree.DecisionTreeClassifier(criterion='gini', max_depth=None, \
                            max_features=None, class_weight=None)
        elif model_name == 'LR':
            model = LogisticRegression(penalty='l2', C=100, tol=0.01, \
                            class_weight=None, solver='liblinear', max_iter=100)
        else:
            # SVM
            model = svm.LinearSVC(penalty='l1', tol=0.1, C=1, dual=False, \
                            class_weight=None, max_iter=100)
        print("Normal training...: {}\n".format(model_name))

    if incUpdate:
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
    with open(para_train['persist_path']+model_name+'.onnx', "wb") as f:
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
                                                    event_id_templates_test, \
                                                    feat_ext_inc=incUpdate)

    # Add weighting factor as we did for training data
    test_x  = weighting.transform(para_test, test_x, term_weighting='tf-idf', \
                                  use_train_factor=True, df_vec_inc=incUpdate)

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
