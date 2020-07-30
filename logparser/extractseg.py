#!/usr/bin/env python3
"""
Description : Extract the segment size from norm logs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import pickle

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

# We only need do it for train dataset
norm_file_loc = parentdir + '/logs/train_norm.txt'
results_loc = parentdir + '/results/train'
seg_vector_file = results_loc + '/train_norm.txt_seg.pkl'

# Create results/ and sub-dir train/ if not exist
if not os.path.exists(parentdir+'/results'):
    os.mkdir(parentdir+'/results')

if not os.path.exists(results_loc):
    os.mkdir(results_loc)

#
# Generate the segment size vector from norm file and then remove the sign in norm file
#

# Segment sign pattern
sign_pattern = re.compile(r'segsign: ')

seg_vector = []
norm_logs = []
seg_start = 0

normfile = open(norm_file_loc, 'r')
linesLst = normfile.readlines()

for idx, line in enumerate(linesLst):
    match = sign_pattern.search(line, 24, 33)
    if match:
        seg_vector.append(idx - seg_start)
        seg_start = idx
        newline = sign_pattern.sub('', line, count=1)
    else:
        newline = line

    # Segment sign is removed
    norm_logs.append(newline)

# The last segment size
seg_vector.append(len(linesLst) - seg_start)

normfile.close()

# Save the segment size vector to file
with open(seg_vector_file, 'wb') as fout:
    pickle.dump(seg_vector[1:], fout)

# Overwrite the old norm file with contents that signs are removed
with open(norm_file_loc, 'w+') as fout:
    fout.writelines(norm_logs)
