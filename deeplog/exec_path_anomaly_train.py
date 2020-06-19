#!/usr/bin/env python3
"""
Description : Train the DeepLog model for execution path anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import preprocess_exec as preprocess
import deeplog_model_exec as dme

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
sys.path.append(parentdir)

# Read parameters from the config file
with open(parentdir+'/entrance/deeplog_config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    # Metrics enable
    METRICS_EN = bool(conlines[1].strip() == 'METRICS=1')
    # Read the sliding window size
    WINDOW_SIZE = int(conlines[3].strip().replace('WINDOW_SIZE=', ''))
    # Read the sliding window step size
    WINDOW_STEP = int(conlines[4].strip().replace('WINDOW_STEP=', ''))
    # Read the template library size
    TEMPLATE_LIB_SIZE = int(conlines[5].strip().replace('TEMPLATE_LIB_SIZE=', ''))
    # Read the batch size for training
    BATCH_SIZE = int(conlines[6].strip().replace('BATCH_SIZE=', ''))
    # Read the number of workers for multi-process data
    NUM_WORKERS = int(conlines[7].strip().replace('NUM_WORKERS=', ''))

para_train = {
    'structured_file': parentdir+'/results/train/train_norm.txt_structured.csv',
    'template_lib'   : parentdir+'/results/persist/template_lib.csv',
    'eid_file'       : parentdir+'/results/persist/event_id_deeplog.npy',
    'eid_file_txt'   : parentdir+'/results/persist/event_id_deeplog.txt',
    'data_path'      : parentdir+'/results/train/',
    'persist_path'   : parentdir+'/results/persist/',
    'window_size'    : WINDOW_SIZE,         # unit is log
    'step_size'      : WINDOW_STEP,         # always 1
    'tmplib_size'    : TEMPLATE_LIB_SIZE,
    'train'          : True,
    'metrics_enable' : METRICS_EN,
    'batch_size'     : BATCH_SIZE,
    'num_workers'    : NUM_WORKERS
}

if __name__ == '__main__':
    print("===> Start training the execution path model ...")

    #####################################################################################
    # Load / preprocess data from train norm structured file
    #####################################################################################
    train_data = preprocess.load_data(para_train)

    #####################################################################################
    # Train with DeepLog Model for Execution Path Anomaly
    #####################################################################################
    model = dme.DeepLogExec()