"""
Description : label assistant 
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
#import pandas as pd
#import collections

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

raw_file_loc  = parentdir + '/logs/raw/log_4_3390.txt'
raw_file_labeled_loc  = parentdir + '/logs/raw/log_4_3390_labeled.txt'

# Generate train/test_labeled.txt
rawfile = open(raw_file_loc, 'r', encoding='utf-8-sig')
rawfile_labeled = open(raw_file_labeled_loc, 'w')

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738]
mainTimestampPattern = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)\.(\d{3})|24:00:00\.000)\] ')
# The pattern for the timestamp added by BFC, e.g. [00:00:35 01/01/1970]
#otherTimestampPattern1 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{2}/\d{2}/\d{4}\] \[[a-zA-Z ]*\] ')
# The pattern for the tag of thread
#threadTagPattern = re.compile(r'\[[a-z ]*\] ', re.IGNORECASE)

# The pattern for label itself
labelPattern = re.compile(r'abn: ')

# The patterns for labeling
anomalyPattern0 = re.compile(r'WARNING - CM HAL declared PULSE lost')
anomalyPattern1 = re.compile(r'WARNING - CM HAL failed to acquire sync or lost sync')
anomalyPattern2 = re.compile(r'BcmCmMultiUsHelper::RngRspMsgEvent:  \(Cm Multi US Helper\) ERROR -')
anomalyPattern3 = re.compile(r'Auth Reject - Unauthorized SAID')

anomalyPatterns = [
    anomalyPattern0,
    anomalyPattern1,
    anomalyPattern2,
    anomalyPattern3
]

for line in rawfile:
    matchTS = mainTimestampPattern.match(line)
    if matchTS:
        currentLineTS = matchTS.group(0)
        # Temp remove the main timestamp
        newline = mainTimestampPattern.sub('', line, count=1)
    else:
        newline =line

    # If it is an empty line or already labeled line, simply write then go next line
    if newline in ['\n', '\r\n'] or labelPattern.match(newline):
        # Add back the main timestamp and save the whole line to target file
        newline = currentLineTS + newline
        rawfile_labeled.write(newline)
        continue

    # Match the label patterns then prefix with 'abn: '
    for pattern in anomalyPatterns:
        match = pattern.search(newline)
        if match:
            newline = 'abn: ' + newline
            break

    # Add back the main timestamp and save the whole line to target file
    newline = currentLineTS + newline
    rawfile_labeled.write(newline)

rawfile.close()
rawfile_labeled.close()