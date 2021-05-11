#!/usr/bin/env python3
"""
Description : Extract the sample info for training of Loglab classification
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import sys
import pickle

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

#
# Process the train data or test data
# We need this module on train dataset always
# We need this module on test dataset for validation only
# Do not call this module for prediction
#

#
# The class label 'cxx' was inserted at the first line of each file when generating
# the monolith training file. As each separate training file is one sample, we can
# get the size of each sample and the target class of the sample resides in.
#
# The info format: [(sample_size, sample_class), ...]
# sample_size is int type and unit is log, aka. one line in norm file
# sample_class is str type and can be int after removing the heading char 'c'
#

# Read the config file to check what kind of log type we are processing
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')
    TRAINING = bool(conlines[1].strip() == 'TRAINING=1')

if TRAINING:
    norm_file_loc = parentdir + '/logs/' + LOG_TYPE + '/train_norm.txt'
    results_loc = parentdir + '/results/train/' + LOG_TYPE
    sample_info_file = results_loc + '/train_norm.txt_saminfo.pkl'
else:
    norm_file_loc = parentdir + '/logs/' + LOG_TYPE + '/test_norm.txt'
    results_loc = parentdir + '/results/test/' + LOG_TYPE
    sample_info_file = results_loc + '/test_norm.txt_saminfo.pkl'

# The re pattern for class name
sample_pattern = re.compile(r'c[0-9]{3} ')

sample_info = []
norm_logs = []
sample_start = 0

normfile = open(norm_file_loc, 'r', encoding='utf-8')
lineslst = normfile.readlines()

for idx, line in enumerate(lineslst):
    # Suppose the timestamp with format like '[20190719-08:58:23.738] ' is always there
    match = sample_pattern.search(line, 24, 29)
    if idx == 0 and not match:
        print("Something is wrong with the monolith file, exit!")
        sys.exit(0)
    elif match:
        classname = match.group(0).strip()
        newline = sample_pattern.sub('', line, count=1)
        norm_logs.append(newline)
        if idx == 0:
            classname_last = classname
            continue
        sample_info.append((idx - sample_start, classname_last))
        sample_start = idx
        classname_last = classname
    else:
        norm_logs.append(line)

# The last sample info
sample_info.append((len(lineslst) - sample_start, classname_last))
#print(sample_info)

normfile.close()

# Save the sample size vector to file
with open(sample_info_file, 'wb') as fout:
    pickle.dump(sample_info, fout)

# Overwrite the old norm file with contents that class labels are removed
with open(norm_file_loc, 'w+', encoding='utf-8') as fout:
    fout.writelines(norm_logs)
