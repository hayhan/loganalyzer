#!/usr/bin/env python3
"""
Description : Detecting the timestamp. Only for prediction of (OSS or DeepLog).
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import hashlib
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

# Read the config file
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')
    TRAINING = bool(conlines[1].strip() == 'TRAINING=1')
    METRICSEN = bool(conlines[2].strip() == 'METRICS=1')
    DLOGCONTEXT = bool(conlines[3].strip() == 'MODEL=DEEPLOG')
    OSSCONTEXT = bool(conlines[3].strip() == 'MODEL=OSS')

# Abstract results directories
results_persist_dir = parentdir + '/results/persist/' + LOG_TYPE + '/'
results_test_dir = parentdir + '/results/test/' + LOG_TYPE + '/'

test_struct_file = results_test_dir + 'test_norm.txt_structured.csv'
runtime_para_loc = results_test_dir + 'test_runtime_para.txt'
temp_library_file = results_persist_dir + 'template_lib.csv'

MAX_TIMESTAMP_LENGTH = 50

def detect_timestamp():
    """ Detect timestamp automatically without apriori
        return the offset of log header
    """
    # Load event id from template library
    data_df = pd.read_csv(temp_library_file, usecols=['EventId'],
                          engine='c', na_filter=False, memory_map=True)
    eid_lib = data_df['EventId'].values.tolist()

    # Load old event id and template of each log from structured file
    data_df = pd.read_csv(test_struct_file, usecols=['Content', 'EventTemplate'],
                          engine='c', na_filter=False, memory_map=True)

    content_logs = data_df['Content'].values.tolist()
    temp_logs = data_df['EventTemplate'].values.tolist()
    # Init offset as -1 which means a non LOG_TYPE log file
    log_start_offset = -1

    for _idx, (content, temp) in enumerate(zip(content_logs, temp_logs)):
        # Slice one char at the head of current template, and then hash the remaining
        for i in range(len(temp)):
            if i > MAX_TIMESTAMP_LENGTH:
                break
            temp_tail = temp[i:]
            eid_tail = hashlib.md5(temp_tail.encode('utf-8')).hexdigest()[0:8]
            if eid_tail in eid_lib:
                if i == 0:
                    # No timestamp at all, we can return directly
                    log_start_offset = 0
                    return log_start_offset

                # Take out the first word (append a space) of the template and locate
                # where it is in the raw log (content).
                header = temp[i:].split()[0]+' '
                match = re.search(header, content)
                if match:
                    log_start_offset = match.start()
                    return log_start_offset
                # For some reason we cannot locate the header in the raw log
                # Go to check the next log
                break

    return log_start_offset

# Get the start offset of log in the raw file
log_offset = detect_timestamp()
#print(log_offset)

# Save the log offst value to RESERVE_TS in the test_runtime_para.txt
# -----------------------------------------------------------------------------
# RESERVE_TS == -1: Not valid log file for LOG_TYPE
# RESERVE_TS ==  0: Valid log file without timestamp
# RESERVE_TS >   0: Valid log file with timestamp.
#
# The value represents the width of timestamp and offset of log header
# -----------------------------------------------------------------------------
if (DLOGCONTEXT or OSSCONTEXT) and ((not TRAINING) and (not METRICSEN)):
    with open(runtime_para_loc, 'w') as f:
        f.write('RESERVE_TS='+str(log_offset))
