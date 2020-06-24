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
    # Read the number of hidden size
    HIDDEN_SIZE = int(conlines[8].strip().replace('HIDDEN_SIZE=', ''))
    # Read the number of topk
    TOPK = int(conlines[9].strip().replace('TOPK=', ''))
    # Read the device, cpu or gpu
    DEVICE = conlines[10].strip().replace('DEVICE=', '')

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
    'metrics_enable' : METRICS_EN
}


if __name__ == '__main__':
    print("===> Start training the execution path model ...")

    #####################################################################################
    # Load / preprocess data from train norm structured file
    #####################################################################################
    train_data_dict, voc_size = preprocess.load_data(para_train)

    #####################################################################################
    # Feed the pytorch Dataset / DataLoader to get the iterator / tensors
    #####################################################################################
    train_data_loader = preprocess.DeepLogExecDataset(train_data_dict,
                                                      batch_size=BATCH_SIZE,
                                                      shuffle=True,
                                                      num_workers=NUM_WORKERS).loader

    #####################################################################################
    # Train with DeepLog Model for Execution Path Anomaly
    #####################################################################################
    #model = dme.DeepLogExec(num_classes=voc_size, hidden_size=HIDDEN_SIZE, num_classes=2,
    #                        num_dir=1, topk=TOPK, device=DEVICE)

    i = 0
    for batch_input in train_data_loader:
        #y = batch_input['EventSeq'].view(-1, 10, 1)
        print(batch_input['EventSeq'])
        #batch_size = y.size()[0]
        #print(batch_input['EventSeq'].view(batch_size, -1, 1))


    import torch
    from torch.utils.data import TensorDataset, DataLoader
    inputs = [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15]]
    outputs = [91, 92, 93]
    dataset = TensorDataset(torch.tensor(inputs, dtype=torch.float), torch.tensor(outputs, dtype=torch.int64))
    dataloader = DataLoader(dataset, batch_size=2, shuffle=True, pin_memory=True)

    for step, (seq, label) in enumerate(dataloader):
        #print(seq.view(-1, 5, 1))
        #seq = seq.clone().detach().view(-1, window_size, input_size).to(device)
        print(step)
