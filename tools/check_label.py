"""
Description : Compare the labels between train/test_labeled.txt and train/test_new_labeled.txt
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
#import pandas as pd
#import collections

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

"""
# For train files
new_file_labeled_loc  = parentdir + '/logs/train_new_labeled.txt'
raw_file_labeled_loc  = parentdir + '/logs/train_labeled.txt'
"""

# For test files
new_file_labeled_loc  = parentdir + '/logs/test_new_labeled.txt'
raw_file_labeled_loc  = parentdir + '/logs/test_labeled.txt'

# Generate train/test_labeled.txt
newfile_labeled = open(new_file_labeled_loc, 'r')
rawfile_labeled = open(raw_file_labeled_loc, 'r')

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738]
mainTimestampPattern = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)\.(\d{3})|24:00:00\.000)\] ')
labelPattern = re.compile(r'abn: ')

raw_labeled_timestampList = []
new_labeled_timestampList = []

for line in newfile_labeled:
    # If the line is labeled, save the main timestamp
    if labelPattern.search(line):
        matchTS = mainTimestampPattern.match(line)
        currentLineTS = matchTS.group(0) + '\n'
        new_labeled_timestampList.append(currentLineTS)

for line in rawfile_labeled:
    # If the line is labeled, save the main timestamp
    if labelPattern.search(line):
        matchTS = mainTimestampPattern.match(line)
        currentLineTS = matchTS.group(0) + '\n'
        raw_labeled_timestampList.append(currentLineTS)

"""
raw_dup_loc  = parentdir + '/tmp/raw_dup_train_1.txt'
new_dup_loc  = parentdir + '/tmp/new_dup_train_1.txt'
"""

raw_dup_loc  = parentdir + '/tmp/raw_dup_test_1.txt'
new_dup_loc  = parentdir + '/tmp/new_dup_test_1.txt'

raw_dup_file = open(raw_dup_loc, 'w')
new_dup_file = open(new_dup_loc, 'w')

raw_dup_file.writelines(raw_labeled_timestampList)
new_dup_file.writelines(new_labeled_timestampList)

raw_dup_file.close()
new_dup_file.close()

newfile_labeled.close()
rawfile_labeled.close()