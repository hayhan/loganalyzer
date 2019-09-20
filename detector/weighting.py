"""
Description : The interface to weight the event log matrix.
Author      : LogPAI Team, modified by Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import numpy as np
import re
import sys
from collections import Counter
from scipy.special import expit
from itertools import compress

def fit_transform(para, X_seq, term_weighting=None, normalization=None):
    """ Fit and transform the data matrix

    Arguments
    ---------
        para: parameter dict
        X_seq: ndarray, log sequences matrix
        term_weighting: None or `tf-idf`
        normalization: None or `zero-mean`

    Returns
    -------
        X_new: The transformed train data matrix
    """
    print('====== Transformed train data summary ======')

    X = X_seq
    num_instance, num_event = X.shape
    #print(X.shape)
    if term_weighting == 'tf-idf':
        df_vec = np.sum(X > 0, axis=0)
        #print(df_vec)
        idf_vec = np.log(num_instance / (df_vec + 1e-8))
        idf_matrix = X * np.tile(idf_vec, (num_instance, 1)) 
        X = idf_matrix
        # Save the idf_vec for predict
        np.save(para['persist_path']+'idf_vector_train.npy', idf_vec)
    if normalization == 'zero-mean':
        mean_vec_t = X.mean(axis=0)
        mean_vec = mean_vec_t.reshape(1, num_event)
        X = X - np.tile(mean_vec, (num_instance, 1))
    elif normalization == 'sigmoid':
        X[X != 0] = expit(X[X != 0])
    X_new = X
    #print(X_new)

    x_data_file = para['data_path'] + 'train_x_data.txt'
    np.savetxt(x_data_file, X_new, fmt="%s")
    print('Final train data shape: {}-by-{}\n'.format(X_new.shape[0], X_new.shape[1]))
    return X_new

def transform(para, X_seq, term_weighting=None, normalization=None, use_train_factor=True):
    """ Transform the data matrix with trained parameters

    Arguments
    ---------
        para: parameter dict
        X_seq: log sequences matrix
        term_weighting: None or `tf-idf`

    Returns
    -------
        X_new: The transformed data matrix
    """
    print('====== Transformed test data summary ======')

    X = X_seq
    num_instance, num_event = X.shape
    if term_weighting == 'tf-idf':
        if use_train_factor:
            # Load the idf vector of training stage from file
            idf_vec = np.load(para['persist_path']+'idf_vector_train.npy')
            #print(idf_vec)
        else:
            # Use the idf data of test instead of the one from train data
            df_vec = np.sum(X > 0, axis=0)
            idf_vec = np.log(num_instance / (df_vec + 1e-8))
        idf_matrix = X * np.tile(idf_vec, (num_instance, 1)) 
        X = idf_matrix
    if normalization == 'zero-mean':
        # ToDo: Use the mean_vec from train stage
        mean_vec_t = X.mean(axis=0)
        mean_vec = mean_vec_t.reshape(1, num_event)
        X = X - np.tile(mean_vec, (num_instance, 1))
    elif normalization == 'sigmoid':
        X[X != 0] = expit(X[X != 0])
    X_new = X
    #print(X_new)

    x_data_file = para['data_path'] + 'test_x_data.txt'
    np.savetxt(x_data_file, X_new, fmt="%s")
    print('Test data shape: {}-by-{}\n'.format(X_new.shape[0], X_new.shape[1])) 

    return X_new
