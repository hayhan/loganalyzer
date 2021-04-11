#!/usr/bin/env python3
"""
Description : Extract the abnormal label vector from norm logs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

#
# Process the train data or test data
#

# Read the config file to decide
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    TRAINING = bool(conlines[0].strip() == 'TRAINING=1')
    METRICSEN = bool(conlines[1].strip() == 'METRICS=1')

if TRAINING:
    norm_file_loc = parentdir + '/logs/cm/train_norm.txt'
    results_loc   = parentdir + '/results/train'
    label_vector_file = results_loc + '/train_norm.txt_labels.csv'
else:
    # For test dataset if METRICS is disabled, do not extract the label vector
    if not METRICSEN:
        sys.exit(0)
    norm_file_loc = parentdir + '/logs/cm/test_norm.txt'
    results_loc   = parentdir + '/results/test'
    label_vector_file = results_loc + '/test_norm.txt_labels.csv'

# Create results/ and sub-dir train/ and test/ if not exist
if not os.path.exists(parentdir+'/results'):
    os.mkdir(parentdir+'/results')

if not os.path.exists(results_loc):
    os.mkdir(results_loc)

#
# Generate the label vector from norm file and remove the labels in norm file
# _ToDo_: optimize for test dataset if no validation is needed
#

import re
import pandas as pd

# Label pattern
labelPattern = re.compile(r'abn: ')

label_messages = []
linecount = 0
norm_logs = []

with open(norm_file_loc, 'r', encoding='utf-8') as fin:
    for line in fin.readlines():
        try:
            # Suppose the timestamp with format like '[20190719-08:58:23.738] ' is always there
            match = labelPattern.search(line, 24, 29)
            if match:
                label_messages.append('a')
                newline = labelPattern.sub('', line, count=1)
            else:
                label_messages.append('-')
                newline = line

            linecount += 1
            # Label is removed
            norm_logs.append(newline)
        except Exception:
            pass

logdf = pd.DataFrame(label_messages, columns=['Label'])
logdf.insert(0, 'LineId', None)
logdf['LineId'] = [i + 1 for i in range(linecount)]
# Save the label vector to results/train or results/test
logdf.to_csv(label_vector_file, index=False)

# Overwrite the old norm file with contents that labels are removed
with open(norm_file_loc, 'w+', encoding='utf-8') as fin:
    fin.writelines(norm_logs)
