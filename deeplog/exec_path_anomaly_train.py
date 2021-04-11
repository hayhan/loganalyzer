#!/usr/bin/env python3
"""
Description : Train the DeepLog model for execution path anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import torch
import torch.nn as nn
import torch.optim as optim

import preprocess_exec as preprocess
from deeplog_models import DeepLogExec
from tqdm import tqdm

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
sys.path.append(parentdir)

# Read parameters from the config file
with open(parentdir+'/entrance/deeplog_config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    # The log type
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')
    # Metrics enable
    METRICS_EN = bool(conlines[2].strip() == 'METRICS=1')
    # Read the sliding window size
    WINDOW_SIZE = int(conlines[4].strip().replace('WINDOW_SIZE=', ''))
    # Read the template library size
    TEMPLATE_LIB_SIZE = int(conlines[5].strip().replace('TEMPLATE_LIB_SIZE=', ''))
    # Read the batch size for training
    BATCH_SIZE = int(conlines[6].strip().replace('BATCH_SIZE=', ''))
    # Read the number of epochs for training
    NUM_EPOCHS = int(conlines[7].strip().replace('NUM_EPOCHS=', ''))
    # Read the number of workers for multi-process data
    NUM_WORKERS = int(conlines[8].strip().replace('NUM_WORKERS=', ''))
    # Read the number of hidden size
    HIDDEN_SIZE = int(conlines[9].strip().replace('HIDDEN_SIZE=', ''))
    # Read the number of topk
    TOPK = int(conlines[10].strip().replace('TOPK=', ''))
    # Read the device, cpu or gpu
    DEVICE = conlines[11].strip().replace('DEVICE=', '')
    # Read num of directions to train
    NUM_DIR = int(conlines[12].strip().replace('NUM_DIR=', ''))

# Abstract results directories
results_persist_dir = parentdir + '/results/persist/' + LOG_TYPE + '/'
results_train_dir = parentdir + '/results/train/' + LOG_TYPE + '/'
results_test_dir = parentdir + '/results/test/' + LOG_TYPE + '/'

para_train = {
    'structured_file': results_train_dir+'train_norm.txt_structured.csv',
    'session_file'   : results_train_dir+'train_norm.txt_session.pkl',
    'template_lib'   : results_persist_dir+'template_lib.csv',
    'eid_file'       : results_persist_dir+'event_id_deeplog.npy',
    'eid_file_txt'   : results_persist_dir+'event_id_deeplog.txt',
    'data_path'      : results_train_dir,
    'persist_path'   : results_persist_dir,
    'window_size'    : WINDOW_SIZE,         # aka sequence length, unit is log
    'tmplib_size'    : TEMPLATE_LIB_SIZE,
    'train'          : True,
    'metrics_enable' : METRICS_EN
}

para_test = {
    'structured_file': results_test_dir+'test_norm.txt_structured.csv',
    'session_file'   : results_test_dir+'test_norm.txt_session.pkl',
    'labels_file'    : results_test_dir+'test_norm.txt_labels.csv',
    'template_lib'   : results_persist_dir+'template_lib.csv',
    'eid_file'       : results_persist_dir+'event_id_deeplog.npy',
    'eid_file_txt'   : results_persist_dir+'event_id_deeplog.txt',
    'data_path'      : results_test_dir,
    'persist_path'   : results_persist_dir,
    'window_size'    : WINDOW_SIZE,         # aka sequence length, unit is log
    'tmplib_size'    : TEMPLATE_LIB_SIZE,
    'train'          : False,
    'metrics_enable' : METRICS_EN
}


if __name__ == '__main__':
    # On Windows, the top level env '__main__' is needed for multi-process dataloading
    # under pytorch framework. On Unix like system, it is not cecessary. See link below
    # https://pytorch.org/docs/stable/data.html#platform-specific-behaviors

    #####################################################################################
    # Train the model
    #####################################################################################
    print("===> Start training the execution path model ...")

    #
    # 1. Load / preprocess data from train norm structured file
    #
    train_data_dict, voc_size = preprocess.load_data(para_train)
    voc_size = TEMPLATE_LIB_SIZE

    #
    # 2. Feed the pytorch Dataset / DataLoader to get the iterator / tensors
    #
    train_data_loader = preprocess.DeepLogExecDataset(train_data_dict,
                                                      batch_size=BATCH_SIZE,
                                                      shuffle=True,
                                                      num_workers=NUM_WORKERS).loader

    #
    # 3. Build DeepLog Model for Execution Path Anomaly Detection
    #
    device = torch.device('cuda' if DEVICE != 'cpu' and torch.cuda.is_available() else 'cpu')
    model = DeepLogExec(device, num_classes=voc_size, hidden_size=HIDDEN_SIZE, num_layers=2,
                        num_dir=NUM_DIR)

    #
    # 4. Start training the model
    #

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
            pbar = tqdm(total=batch_cnt, unit='Batches', disable=False,
                        ncols=0)
            for batch_in in train_data_loader:
                # Forward pass
                # Each batch is a dict in the dataloader, in which the value is tensor
                # batch_in['EventSeq'] is a 2-Dimension tensor (batch_size x seq_len)
                # The tensor of input sequences to model should be 3-Dimension as below
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

                # Update the progress bar
                pbar.update(1)
            pbar.close()
            epoch_loss = epoch_loss / batch_cnt
            print("Epoch {}/{}, train loss: {:.5f}".format(epoch+1, NUM_EPOCHS, epoch_loss))

    # Enclose the process of evalating
    def evaluate(data_loader):
        """ Block that evaluate the model
        """
        _anomaly_pred = []
        _t_p = _t_n = _f_p = _f_n = 0
        model.eval()
        with torch.no_grad():
            for batch_in in data_loader:
                seq = batch_in['EventSeq'].clone().detach().view(-1, WINDOW_SIZE, 1).to(device)
                output = model(seq)
                #pred_prob = output.softmax(dim=-1)
                #pred_sort = torch.argsort(pred_prob, 1, True)
                pred_sort = torch.argsort(output, 1, True)
                bt_size = pred_sort.size(0)
                #topk_val = torch.narrow(pred_sort, 1, 0, 10)
                #print('debug topk1:', topk_val)
                seq_pred_sort = pred_sort.tolist()
                seq_target = batch_in['Target'].tolist()
                seq_label = batch_in['Label'].tolist()
                #topk_lst = []
                for i in range(bt_size):
                    #topk_lst.append(seq_pred_sort[i].index(seq_target[i]))
                    top_idx = seq_pred_sort[i].index(seq_target[i])
                    if seq_label[i] == 1:
                        if top_idx >= TOPK:
                            _t_p += 1
                            _anomaly_pred.append(1)
                        else:
                            _f_n += 1
                            _anomaly_pred.append(0)
                    else:
                        if top_idx >= TOPK:
                            _anomaly_pred.append(1)
                            _f_p += 1
                        else:
                            _anomaly_pred.append(0)
                            _t_n += 1
                #print('debug topk2:', topk_lst)

        return _t_p, _f_p, _t_n, _f_n, _anomaly_pred

    # Train the model now
    train()

    # Evaluate with itself
    t_p, f_p, t_n, f_n, _ = evaluate(train_data_loader)
    print('Train Dataset Validation ==> TP: {}, FP: {}, TN: {}, FN: {}' \
          .format(t_p, f_p, t_n, f_n))

    #
    # 5. Serialize the model
    #
    torch.save(model.state_dict(),
               para_train['persist_path']+'model_deeplog_exec_win'+str(WINDOW_SIZE)+'.pt')

    #####################################################################################
    # Evaluate the model with test dataset
    #####################################################################################
    print("===> Start evaluating the execution path model ...")

    #
    # 1. Load / preprocess test dataset for validation
    #
    test_data_dict, _ = preprocess.load_data(para_test)
    #print(test_data_dict['EventSeq'])
    #print(test_data_dict['Target'])

    #
    # 2. Feed the pytorch Dataset / DataLoader with test dataset
    #
    test_data_loader = preprocess.DeepLogExecDataset(test_data_dict,
                                                     batch_size=BATCH_SIZE,
                                                     shuffle=False,
                                                     num_workers=NUM_WORKERS).loader

    #
    # 3. Start evaluating the model with test dataset
    #
    t_p, f_p, t_n, f_n, anomaly_pred = evaluate(test_data_loader)
    print('Test Dataset Validation  ==> TP: {}, FP: {}, TN: {}, FN: {}' \
          .format(t_p, f_p, t_n, f_n))

    # Calc the metrics for dataset with anomalies
    if t_p + f_p != 0 and t_p + f_n != 0:
        precision = 100 * t_p / (t_p + f_p)
        recall = 100 * t_p / (t_p + f_n)
        f_1 = 2 * precision * recall / (precision + recall)
        print('Test Dataset Validation  ==>', \
              'Precision: {:.2f}%, Recall: {:.2f}%, F1: {:.2f}%' \
              .format(precision, recall, f_1))

    #print(anomaly_pred)
