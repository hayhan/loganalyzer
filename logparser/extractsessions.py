#!/usr/bin/env python3
"""
Description : Extract the session size from norm logs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import pickle

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

#
# Process the train data or test data
# We need this module on train dataset always
# We need this module on test dataset for validation only
# Do not call this module for prediction
#

# Read the config file to decide
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    TRAINING = bool(conlines[0].strip() == 'TRAINING=1')

if TRAINING:
    norm_file_loc = parentdir + '/logs/train_norm.txt'
    results_loc = parentdir + '/results/train'
    session_file = results_loc + '/train_norm.txt_session.pkl'
else:
    norm_file_loc = parentdir + '/logs/test_norm.txt'
    results_loc = parentdir + '/results/test'
    session_file = results_loc + '/test_norm.txt_session.pkl'

# Create results/ and sub-dir if not exist
if not os.path.exists(parentdir+'/results'):
    os.mkdir(parentdir+'/results')

if not os.path.exists(results_loc):
    os.mkdir(results_loc)

#
# Generate the session size vector from norm file, then remove the labels in norm file
#

# Session label pattern
# The label can be added by both file concatenation and preprocess of logparser
# The same label might be added twice for the log at the beginging of each file
# So we replace the labels with empty by max twice below

# In test dataset for validation, the session label might not exist. Make sure we return
# the correct session vector (aka one element representing the session size) in this case

session_pattern = re.compile(r'segsign: ')

session_vector = []
norm_logs = []
session_start = 0

normfile = open(norm_file_loc, 'r')
linesLst = normfile.readlines()

for idx, line in enumerate(linesLst):
    match = session_pattern.search(line, 24, 33)
    if match:
        newline = session_pattern.sub('', line, count=2)
        if idx != 0:
            session_vector.append(idx - session_start)
            session_start = idx
    else:
        newline = line

    # Session label is removed
    norm_logs.append(newline)

# The last session size
session_vector.append(len(linesLst) - session_start)

normfile.close()

# Save the session size vector to file
with open(session_file, 'wb') as fout:
    pickle.dump(session_vector, fout)

# Overwrite the old norm file with contents that session labels are removed
with open(norm_file_loc, 'w+') as fout:
    fout.writelines(norm_logs)
