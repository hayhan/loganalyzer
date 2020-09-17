#!/usr/bin/env python3
"""
Description : This file does post-processing for test norm strucured CM/DOCSIS logs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import pickle
import hashlib
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

test_norm_pred_file = parentdir + '/logs/test_norm_pred.txt'
test_struct_file = parentdir + '/results/test/test_norm.txt_structured.csv'
temp_library_file = parentdir + '/results/persist/template_lib.csv'
test_struct_pred_file = parentdir + '/results/test/test_norm.txt_structured_pred.csv'
# Two mapping files
# 1) The mapping between raw (test.txt) and norm (test_norm.txt)
rawln_idx_file = parentdir + '/results/test/rawline_idx_norm.pkl'
# 2) The mapping between norm (test_norm.txt) and norm pred (test_norm_pred.txt)
#mapping_norm_pred_file = parentdir + '/results/test/mapping_norm_pred.pkl'

# Special templates, for case 2
SPECIAL_ID = ['b9c1fdb1']

def recover_messed_logs():
    """ Recover CM logs which are messed up by higher priority threads
    """
    # Load event id from template library
    data_df = pd.read_csv(temp_library_file, usecols=['EventId'],
                          engine='c', na_filter=False, memory_map=True)
    eid_lib = data_df['EventId'].values.tolist()

    # Load old event id and template of each log from structured file
    data_df = pd.read_csv(test_struct_file, usecols=['Time', 'EventIdOld', 'EventTemplate'],
                          engine='c', na_filter=False, memory_map=True)
    time_logs = data_df['Time'].values.tolist()
    eid_old_logs = data_df['EventIdOld'].values.tolist()
    temp_logs = data_df['EventTemplate'].values.tolist()

    #new_temp_logs = [0] * data_df.shape[0]
    m1_found = False
    o1_head = ''
    skipped_ln = []
    norm_pred_file = open(test_norm_pred_file, 'w')

    for idx, (eido, temp) in enumerate(zip(eid_old_logs, temp_logs)):
        # Check the first char to see if it is 'L'
        head_l = bool(temp[0] == 'L')
        # Check th next log if current log id exists already in lib or m1 has not been
        # found and the log does not start with char L.
        if (eido != '0') or (not m1_found and not head_l):
            #new_temp_logs[idx] = temp
            norm_pred_file.write(time_logs[idx]+' '+temp+'\n')
            continue

        # We get here only when old event id is zero AND (m1_found OR head_l)
        if m1_found:
            # Abort if we cannot find m2 within 20 logs
            if idx - m1_idx > 20:
                #new_temp_logs[idx] = temp
                norm_pred_file.write(time_logs[idx]+' '+temp+'\n')
                m1_found = False
                continue
            # Note the eido == 0 here
            temp_o1 = o1_head + temp
            #new_temp_logs[idx] = temp_o1
            norm_pred_file.write(time_logs[idx]+' '+temp_o1+'\n')
            m1_found = False
            continue

        # We get here only when old event id is zero AND (m1_found==0 AND head_l=='L')
        # The case 1, the most common case
        for i in range(len(temp)):
            o1_head = temp[0:i+1]
            temp_o2 = temp[i+1:]
            eid_o2 = hashlib.md5(temp_o2.encode('utf-8')).hexdigest()[0:8]
            if eid_o2 in eid_lib:
                m1_found = True
                m1_idx = idx
                #new_temp_logs[idx] = temp_o2
                norm_pred_file.write(time_logs[idx]+' '+temp_o2+'\n')
                if eid_o2 in SPECIAL_ID:
                    # Remove one trailing spaces in o1_head, the case 2
                    o1_head = o1_head[0:-1]
                break

        # If cannot find m1 in current log, we suppose o1 is broken by o2 wherein a
        # leading new line char exist. In other words, we get here w/ m1_found == False
        # because we are encountering case 3.
        if not m1_found:
            # Skip writing the empty line to norm pred file
            # norm_pred_file.write(time_logs[idx]+' '+'\n')
            # new_temp_logs[idx] = ''

            # We write down the skipped line/log number, which will be used to update
            # the raw / norm file line mapping table: rawline_idx_norm.pkl
            skipped_ln.append(idx)

            # The o1_head now contains the whole m1, so we claim m1 is found
            m1_found = True
            m1_idx = idx

    norm_pred_file.close()

    # Save the new temp/eid vector to a new norm test file
    #--block comment out start--
    #data_df = pd.DataFrame()
    #data_df['EventTemplate'] = new_temp_logs
    #data_df.to_csv(test_struct_pred_file, index=False)
    #--end--

    # Update the raw / norm file line mapping table if needed
    if len(skipped_ln) > 0:
        with open(rawln_idx_file, 'rb') as fio:
            raw_idx_vector_norm = pickle.load(fio)
        # reverse the list in skipped_ln before poping the empty lines
        for i in skipped_ln[::-1]:
            raw_idx_vector_norm.pop(i)
        with open(rawln_idx_file, 'wb') as fio:
            pickle.dump(raw_idx_vector_norm, fio)


#
# Run the post processing here
#
recover_messed_logs()
