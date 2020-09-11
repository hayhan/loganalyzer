#!/usr/bin/env python3
"""
Description : This file does post-processing for test norm strucured CM/DOCSIS logs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import hashlib
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

test_structured_file = parentdir + '/results/test/test_norm.txt_structured.csv'
temp_library_file = parentdir + '/results/persist/template_lib.csv'
test_structured_pred_file = parentdir + '/results/test/test_norm.txt_structured_pred.csv'

# Special templates
SPECIAL_ID = ['b9c1fdb1']

def recover_messed_logs():
    """ Recover CM logs which are messed up by higher priority threads
    """
    # Load event id from template library
    data_df = pd.read_csv(temp_library_file, usecols=['EventId'],
                          engine='c', na_filter=False, memory_map=True)
    eid_lib = data_df['EventId'].values.tolist()

    # Load old event id and template of each log from structured file
    data_df = pd.read_csv(test_structured_file, usecols=['EventIdOld', 'EventTemplate'],
                          engine='c', na_filter=False, memory_map=True)
    eid_old_logs = data_df['EventIdOld'].values.tolist()
    temp_logs = data_df['EventTemplate'].values.tolist()

    new_eid_logs = [0] * data_df.shape[0]
    new_temp_logs = [0] * data_df.shape[0]
    m1_found = False
    o1_head = ''

    for idx, (eido, temp) in enumerate(zip(eid_old_logs, temp_logs)):
        # Check the first char to see if it is 'L'
        head_l = bool(temp[0] == 'L')
        # Check th next log if current log id exists already in lib or m1 has not been
        # found and the log does not start with char L.
        if (eido != '0') or (not m1_found and not head_l):
            new_temp_logs[idx] = temp
            if eido != '0':
                new_eid_logs[idx] = eido
            else:
                new_eid_logs[idx] = hashlib.md5(temp.encode('utf-8')).hexdigest()[0:8]
            continue

        # We get here only when old event id is zero AND (m1_found OR head_l)
        if m1_found:
            if eido == '0':
                temp_o1 = o1_head + temp
                new_temp_logs[idx] = temp_o1
                new_eid_logs[idx] = hashlib.md5(temp_o1.encode('utf-8')).hexdigest()[0:8]
                m1_found = False
            continue

        # We get here only when old event id is zero AND (m1_found==0 AND head_l=='L')
        for i in range(len(temp)):
            o1_head = temp[0:i+1]
            temp_o2 = temp[i+1:]
            eid_o2 = hashlib.md5(temp_o2.encode('utf-8')).hexdigest()[0:8]
            if eid_o2 in eid_lib:
                m1_found = True
                new_temp_logs[idx] = temp_o2
                new_eid_logs[idx] = eid_o2
                if eid_o2 in SPECIAL_ID:
                    # Remove one trailing spaces in o1_head
                    o1_head = o1_head[0:-1]
                break

        # If cannot find m1 in current log, we suppose it is a good new template
        if not m1_found:
            new_temp_logs[idx] = temp
            new_eid_logs[idx] = hashlib.md5(temp.encode('utf-8')).hexdigest()[0:8]

    # Save the new temp/eid vector to a new norm test file
    data_df = pd.DataFrame()
    data_df['EventId'] = new_eid_logs
    data_df['EventTemplate'] = new_temp_logs
    data_df.to_csv(test_structured_pred_file, index=False)


#
# Run the post processing here
#
recover_messed_logs()
