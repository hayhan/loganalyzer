#!/usr/bin/env python3
"""
Description : Train the DeepLog model for execution path anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
from collections import defaultdict
#from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score
import torch
import torch.nn as nn
import torch.optim as optim

import preprocess_exec as preprocess
from deeplog_models import DeepLogExec

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
    # Read the template library size
    TEMPLATE_LIB_SIZE = int(conlines[4].strip().replace('TEMPLATE_LIB_SIZE=', ''))
    # Read the batch size for training
    BATCH_SIZE = int(conlines[5].strip().replace('BATCH_SIZE=', ''))
    # Read the number of epochs for training
    NUM_EPOCHS = int(conlines[6].strip().replace('NUM_EPOCHS=', ''))
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
    'window_size'    : WINDOW_SIZE,         # aka sequence length, unit is log
    'tmplib_size'    : TEMPLATE_LIB_SIZE,
    'train'          : True,
    'metrics_enable' : METRICS_EN
}

para_test = {
    'structured_file': parentdir+'/results/test/test_norm.txt_structured.csv',
    'template_lib'   : parentdir+'/results/persist/template_lib.csv',
    'eid_file'       : parentdir+'/results/persist/event_id_deeplog.npy',
    'eid_file_txt'   : parentdir+'/results/persist/event_id_deeplog.txt',
    'data_path'      : parentdir+'/results/test/',
    'persist_path'   : parentdir+'/results/persist/',
    'window_size'    : WINDOW_SIZE,         # aka sequence length, unit is log
    'tmplib_size'    : TEMPLATE_LIB_SIZE,
    'train'          : False,
    'metrics_enable' : METRICS_EN
}


if __name__ == '__main__':
    # On Windows, the top level env '__main__' is needed for multi-process dataloading
    # under pytorch framework. On Unix like system, it is not cecessary. See link below
    # https://pytorch.org/docs/stable/data.html#platform-specific-behaviors

    print("===> Start training the execution path model ...")

    #####################################################################################
    # Load / preprocess data from train norm structured file
    #####################################################################################
    train_data_dict, voc_size = preprocess.load_data(para_train)
    voc_size = TEMPLATE_LIB_SIZE
    #print(train_data_dict['EventSeq'])

    #####################################################################################
    # Feed the pytorch Dataset / DataLoader to get the iterator / tensors
    #####################################################################################
    train_data_loader = preprocess.DeepLogExecDataset(train_data_dict,
                                                      batch_size=BATCH_SIZE,
                                                      shuffle=True,
                                                      num_workers=NUM_WORKERS).loader

    #####################################################################################
    # Build DeepLog Model for Execution Path Anomaly Detection
    #####################################################################################
    device = torch.device('cuda' if DEVICE != 'cpu' and torch.cuda.is_available() else 'cpu')
    model = DeepLogExec(device, num_classes=voc_size, hidden_size=HIDDEN_SIZE, num_layers=2,
                        num_dir=1, topk=TOPK)

    # Select the loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())

    # Enclose the process of training
    def train():
        """ Block that trains the model
        """
        model.train()
        batch_cnt = len(train_data_loader)
        for epoch in range(NUM_EPOCHS):
            epoch_loss = 0
            for batch_in in train_data_loader:
                # Forward pass
                # Each batch is a dict in the dataloader, in which the value is tensor
                # batch_in['EventSeq'] is a 2-Dimension tensor (batch_size x seq_len)
                # The tensor of input sequences to model shold be 3-Dimension as below
                # (batch_size x seq_len x input_size)
                seq = batch_in['EventSeq'].clone().detach().view(-1, WINDOW_SIZE, 1).to(device)
                output = model(seq)
                # The output of mdoel is 2-D tensor (batch_size x num_classes)
                # batch_in['Target'] is a 1-D tensor (batch_size)
                # The Target (class index) should be within [0, num_classes-1]
                loss = criterion(output, batch_in['Target'].long().view(-1).to(device))

                # Backward pass and optimize
                optimizer.zero_grad()
                loss.backward()
                epoch_loss += loss.item()
                optimizer.step()
            epoch_loss = epoch_loss / batch_cnt
            print("Epoch {}/{}, train loss: {:.5f}".format(epoch+1, NUM_EPOCHS, epoch_loss))

    # Enclose the process of evalating
    def evaluate(data_loader):
        """ Block that evaluate the model
        """
        model.eval()
        with torch.no_grad():
            #print(len(data_loader))
            y_pred = []
            store_dict = defaultdict(list)
            for batch_in in data_loader:
                seq = batch_in['EventSeq'].clone().detach().view(-1, WINDOW_SIZE, 1).to(device)
                output = model(seq)
                y_pred = output.softmax(dim=-1)
                window_prob, window_pred = torch.max(y_pred, 1)
                print(window_prob, window_pred)

    # Train the model now
    train()
    #evaluate(train_data_loader)

    #####################################################################################
    # Load / preprocess validation data
    #####################################################################################
    test_data_dict, voc_size = preprocess.load_data(para_test)
    print(test_data_dict['EventSeq'])
    print(test_data_dict['Target'])

    #####################################################################################
    # Feed the pytorch Dataset / DataLoader with validation data
    #####################################################################################
    test_data_loader = preprocess.DeepLogExecDataset(test_data_dict,
                                                     batch_size=BATCH_SIZE,
                                                     shuffle=True,
                                                     num_workers=NUM_WORKERS).loader
    # Evaluate the test dataset
    evaluate(test_data_loader)
