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

if __name__ == '__main__':
    raw_data, event_mapping_data = dataloader.load_DOCSIS()
    #print(raw_data)
    #print(event_mapping_data)

    dataloader.add_sliding_window(raw_data, event_mapping_data)
    """
    feature_extractor = preprocessing.FeatureExtractor()
    x_train = feature_extractor.fit_transform(x_train, term_weighting='tf-idf')

    x_test = feature_extractor.transform(x_test)

    model = DecisionTree()
    model.fit(x_train, y_train)

    print('Train validation:')
    precision, recall, f1 = model.evaluate(x_train, y_train)

    print('Test validation:')
    precision, recall, f1 = model.evaluate(x_test, y_test)
    """