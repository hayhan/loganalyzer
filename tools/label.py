"""
Description : label the train/test.txt from existing train/test_new_labeled.txt 
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
#import pandas as pd
import collections

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

# For train files
raw_file_loc  = parentdir + '/logs/train.txt'
new_file_labeled_loc  = parentdir + '/logs/train_new_labeled.txt'
raw_file_labeled_loc  = parentdir + '/logs/train_labeled.txt'

"""
# For test files
raw_file_loc  = parentdir + '/logs/test.txt'
new_file_labeled_loc  = parentdir + '/logs/test_new_labeled.txt'
raw_file_labeled_loc  = parentdir + '/logs/test_labeled.txt'
"""

# Generate train/test_labeled.txt
rawfile = open(raw_file_loc, 'r')
newfile_labeled = open(new_file_labeled_loc, 'r')
rawfile_labeled = open(raw_file_labeled_loc, 'w')

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738]
mainTimestampPattern = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)\.(\d{3})|24:00:00\.000)\] ')
labelPattern = re.compile(r'abn: ')

raw_timestampList = []
timestampList = []
processFlag = []
for line in newfile_labeled:
    # If the line is labeled, save the main timestamp
    if labelPattern.search(line):
        matchTS = mainTimestampPattern.match(line)
        currentLineTS = matchTS.group(0)
        timestampList.append(currentLineTS)
        processFlag.append(0)

for line in rawfile:
    matchTS = mainTimestampPattern.match(line)
    if matchTS:
        currentLineTS = matchTS.group(0)
        raw_timestampList.append(currentLineTS)
        # Temp remove the main timestamp
        newline = mainTimestampPattern.sub('', line, count=1)
    else:
        newline =line

    # If it is an empty line, simply write then go next line
    if newline in ['\n', '\r\n']:
        # Add back the main timestamp and save the whole line to target file
        newline = currentLineTS + newline
        rawfile_labeled.write(newline)
        continue

    if currentLineTS in timestampList:
        newline = 'abn: ' + newline

    # Add back the main timestamp and save the whole line to target file
    newline = currentLineTS + newline
    rawfile_labeled.write(newline)

rawfile.close()
newfile_labeled.close()
rawfile_labeled.close()

# Check the duplicates of main timestamp, and then
# manually double check the train/test_labeled.txt
# raw_timestampList
# timestampList
raw_dup = [item for item, count in collections.Counter(raw_timestampList).items() if count > 1]
new_dup = [item for item, count in collections.Counter(timestampList).items() if count > 1]

raw_dup_loc  = parentdir + '/tmp/raw_dup_train.txt'
new_dup_loc  = parentdir + '/tmp/new_dup_train.txt'

"""
raw_dup_loc  = parentdir + '/tmp/raw_dup_test.txt'
new_dup_loc  = parentdir + '/tmp/new_dup_test.txt'
"""

raw_dup_file = open(raw_dup_loc, 'w')
new_dup_file = open(new_dup_loc, 'w')

raw_dup_file.writelines(raw_dup)
new_dup_file.writelines(new_dup)

raw_dup_file.close()
new_dup_file.close()