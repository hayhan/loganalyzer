#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(grandpadir)

from detector.models import DecisionTree
from extractor import dataloader, featurextor

#struct_log = '../data/HDFS/HDFS_100k.log_structured_short.csv' # The structured log file
#label_file = '../data/HDFS/anomaly_label.csv' # The anomaly label file

para = {
    'labeled_file'   : grandpadir+'/results/test_norm.txt_labeled.csv',
    'structured_file': grandpadir+'/results/test_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/test_norm.txt_templates.csv',
    'window_path'    : grandpadir+'/results/windows',
    'window_size'    : 10000,    # milliseconds
    'step_size'      : 5000,     # milliseconds
    'train_ratio'    : 0.7
}

if __name__ == '__main__':
    raw_data, event_mapping_data, event_id_templates = dataloader.load_DOCSIS(para)
    #print(raw_data)
    #print(event_mapping_data)
    #print(event_id_templates)

    event_count_matrix, labels = dataloader.add_sliding_window(para, raw_data, event_mapping_data, event_id_templates)
    #print(event_count_matrix)
    #print(labels)

    # Split event_count_matrix into train and test data sets
    num_train = int(para['train_ratio'] * len(labels))
    train_x = event_count_matrix[0:num_train]
    train_y = labels[0:num_train]
    print('there are %d instances in train dataset,'% len(train_y), '%d are anomalies'%sum(train_y))

    test_x = event_count_matrix[num_train:]
    test_y = labels[num_train:]
    print('there are %d instances in test dataset,'% len(test_y), '%d are anomalies'%sum(test_y))

    feature_extractor = featurextor.FeatureExtractor()
    train_x = feature_extractor.fit_transform(para, train_x, term_weighting='tf-idf', is_train=1)
    test_x  = feature_extractor.fit_transform(para, test_x, term_weighting='tf-idf', is_train=0)

    """
    feature_extractor = preprocessing.FeatureExtractor()
    x_train = feature_extractor.fit_transform(x_train, term_weighting='tf-idf')

    x_test = feature_extractor.transform(x_test)
    """
    model = DecisionTree()
    model.fit(train_x, train_y)

    print('Train validation:')
    precision, recall, f1 = model.evaluate(train_x, train_y)

    print('Test validation:')
    precision, recall, f1 = model.evaluate(test_x, test_y)
    