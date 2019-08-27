#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(grandpadir)

from detector.models import SVM
from extractor import dataloader, featurextor


para = {
    'labeled_file'   : grandpadir+'/results/test_norm.txt_labeled.csv',
    'structured_file': grandpadir+'/results/test_norm.txt_structured.csv',
    'templates_file' : grandpadir+'/results/test_norm.txt_templates.csv',
    'window_path'    : grandpadir+'/results/windows',
    'window_size'    : 10000,    # milliseconds
    'step_size'      : 5000,     # milliseconds
    'train_ratio'    : 0.8
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
    train_x = feature_extractor.fit_transform(para, train_x, term_weighting='tf-idf')
    test_x  = feature_extractor.transform(para, test_x)

    model = SVM()
    model.fit(train_x, train_y)

    test_y_pred = model.predict(test_x)
    np.savetxt(para['window_path']+'/test_y_data.txt', test_y, fmt="%s")
    np.savetxt(para['window_path']+'/test_y_data_pred.txt', test_y_pred, fmt="%s")
    """
    print('Train validation:')
    precision, recall, f1 = model.evaluate(train_x, train_y)

    print('Test validation:')
    precision, recall, f1 = model.evaluate(test_x, test_y)
    """