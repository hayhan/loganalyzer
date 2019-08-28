#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(grandpadir)

from detector.models import DecisionTree
from extractor import dataloader, featurextor

para_train = {
    'labeled_file'   : grandpadir+'/results/train/train_norm.txt_labeled.csv',
    'structured_file': grandpadir+'/results/train/train_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/train/train_norm.txt_templates.csv',
    'data_path'      : grandpadir+'/results/train/',
    'eventid_shuf'   : grandpadir+'/results/',
    'window_size'    : 10000,    # milliseconds
    'step_size'      : 5000,     # milliseconds
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}

para_test = {
    'labeled_file'   : grandpadir+'/results/test/test_norm.txt_labeled.csv',
    'structured_file': grandpadir+'/results/test/test_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/test/test_norm.txt_templates.csv',
    'data_path'      : grandpadir+'/results/test/',
    'eventid_shuf'   : grandpadir+'/results/',
    'window_size'    : 10000,    # milliseconds
    'step_size'      : 5000,     # milliseconds
    'train_ratio'    : 0.8       # not used anymore after de-coupling train/test data
}

if __name__ == '__main__':
    """
    Feature extraction for the train data
    """
    # Load the train data from files and do some pre-processing
    raw_data_train, \
    event_mapping_data_train, \
    event_id_templates_train = dataloader.load_DOCSIS(para_train)

    # Add sliding window and create the event count matrix for the train data set
    # All the EventId in templates are shuffed and saved under results folder
    train_x, train_y = dataloader.add_sliding_window(para_train, raw_data_train, \
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
    feature_extractor = featurextor.FeatureExtractor()
    train_x = feature_extractor.fit_transform(para_train, train_x, term_weighting='tf-idf')

    """
    Train the data now
    """
    model = DecisionTree()
    model.fit(train_x, train_y)

    """
    Feature extraction for the test data
    """
    # Load the test data from files and do some pre-processing
    raw_data_test, \
    event_mapping_data_test, \
    event_id_templates_test = dataloader.load_DOCSIS(para_test)
    
    # Add sliding window and create the event count matrix for the test data set.
    # The input parameter event_id_templates_test is not used actually, we reuse
    # the saved shuffled EventId list in the training step.
    test_x, test_y = dataloader.add_sliding_window(para_test, raw_data_test, \
                                                   event_mapping_data_test, \
                                                   event_id_templates_test)

    # Add weighting factor as we did for training data
    test_x  = feature_extractor.transform(para_test, test_x, use_train_factor=True)

    #test_y_pred = model.predict(test_x)
    #np.savetxt(para_test['data_path']+'test_y_data.txt', test_y, fmt="%s")
    #np.savetxt(para_test['data_path']+'test_y_data_pred.txt', test_y_pred, fmt="%s")

    print('Train validation:')
    precision, recall, f1 = model.evaluate(train_x, train_y)

    print('Test validation:')
    precision, recall, f1 = model.evaluate(test_x, test_y)
