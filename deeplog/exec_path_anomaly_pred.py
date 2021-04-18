#!/usr/bin/env python3
"""
Description : Predict for execution path anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import pickle
import torch

import preprocess_exec as preprocess
import para_value_anomaly_det as paradet
from deeplog_models import DeepLogExec

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
results_test_dir = parentdir + '/results/test/' + LOG_TYPE + '/'

# Read the runtime parameters
with open(results_test_dir + 'test_runtime_para.txt', 'r') as parafile:
    paralines = parafile.readlines()
    RESERVE_TS = int(paralines[0].strip().replace('RESERVE_TS=', ''))
if RESERVE_TS < 0:
    # Not LOG_TYPE log. Return right now.
    print("You submitted a non {} log. Please check.".format(LOG_TYPE))
    sys.exit(0)

# Parameter dictionary
para_test = {
    'o_struct_file'  : results_test_dir+'test_norm.txt_structured.csv',
    'structured_file': results_test_dir+'test_norm_pred.txt_structured.csv',
    'labels_file'    : results_test_dir+'test_norm.txt_labels.csv',
    'rawln_idx_file' : results_test_dir+'rawline_idx_norm.pkl',
    'map_norm_pred'  : results_test_dir+'mapping_norm_pred.pkl',
    'pred_result'    : results_test_dir+'anomaly_result.txt',
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

    print("===> Start predicting with the execution path model ...")

    #
    # 1. Load / preprocess test dataset
    #
    test_data_dict, voc_size = preprocess.load_data(para_test)
    voc_size = TEMPLATE_LIB_SIZE
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
    # 3. Load the norm and norm pred structured files for the OSS para value detection
    #
    content_lst, eid_lst, template_lst = preprocess.load_oss_data(para_test)

    # Load the mapping vector between norm and norm pred file for the OSS
    with open(para_test['map_norm_pred'], 'rb') as f:
        mnp_vec = pickle.load(f)

    #
    # 4. Load deeplog_exec model back
    #
    device = torch.device('cuda' if DEVICE != 'cpu' and torch.cuda.is_available() else 'cpu')
    model = DeepLogExec(device, num_classes=voc_size, hidden_size=HIDDEN_SIZE, num_layers=2,
                        num_dir=NUM_DIR)
    model.load_state_dict(torch.load(
        para_test['persist_path']+'model_deeplog_exec_win'+str(WINDOW_SIZE)+'.pt'))

    #
    # 5. Predict the test data
    #
    j = 0
    anomaly_pred = []
    anomaly_line = []
    model.eval()
    with torch.no_grad():
        for batch_in in test_data_loader:
            #print(batch_in['EventSeq'])
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
                # The log (line, 0-based) index of anomaly in norm (pred) log file
                norm_idx = i+WINDOW_SIZE+j*BATCH_SIZE
                top_idx = seq_pred_sort[i].index(seq_target[i])

                if top_idx >= TOPK:
                    # Saves each log state from line (WINDOW_SIZE+1) in norm log file
                    anomaly_pred.append(1)
                    # Save anomaly log index of norm file
                    anomaly_line.append(norm_idx)
                else:
                    # Integrate the OSS here as the para value anomaly detection
                    if paradet.para_anomaly_det(content_lst[mnp_vec[norm_idx]], eid_lst[norm_idx],
                                                template_lst[norm_idx]):
                        anomaly_pred.append(1)
                        anomaly_line.append(norm_idx)
                    else:
                        anomaly_pred.append(0)
            #print('debug topk2:', topk_lst)
            j += 1

    #print(anomaly_pred)
    #print(anomaly_line)
    #print(len(anomaly_line))

    #
    # 6. Map anomaly_line[] in norm file to the raw test data file
    #
    # Load the line mapping list between raw and norm test file
    with open(para_test['rawln_idx_file'], 'rb') as f:
        raw_idx_vector_norm = pickle.load(f)

    # Write the final results to a file. It is 1-based line num in raw file
    with open(para_test['pred_result'], 'w') as f:
        for item in anomaly_line:
            f.write('%s\n' % (raw_idx_vector_norm[item]))
