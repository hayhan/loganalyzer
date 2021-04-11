#!/usr/bin/env python3
"""
Description : For detecting the timestamp. Only for prediction of (OSS or DeepLog).
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))

raw_file_loc = grandpadir + '/logs/cm/test.txt'
norm_file_loc = grandpadir + '/logs/cm/test_norm.txt'

rawfile = open(raw_file_loc, 'r', encoding='utf-8-sig')
normfile = open(norm_file_loc, 'w', encoding='utf-8')

# The pattern for CM console prompts
strPattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
# The pattern for the timestamp added by BFC, e.g. [00:00:35 01/01/1970], [11/21/2018 14:49:32]
# or emta specific "00:00:35.012 01/01/1970  "
strPattern2 = re.compile(r'\[?(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)(.\d\d\d)?|24:00:00(.000)?) '
                         r'\d{2}/\d{2}/\d{4}\]?  ?')
strPattern3 = re.compile(r'\[\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)\] ')
# The pattern for the timestamp added by others, e.g. 01/01/1970 00:00:19
strPattern4 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')
# The pattern for the tag of thread
strPattern5 = re.compile(r'\[ ?[a-z][a-z0-9\- ]*\] ', re.IGNORECASE)
strPattern6 = re.compile(r'\+{3} ')
# The pattern for the instance name of BFC class
strPattern7 = re.compile(r'(?<=:  )\([a-zA-Z0-9/ ]+\) ')

strPatterns = [
    strPattern1, strPattern2, strPattern3, strPattern4,
    strPattern5, strPattern6, strPattern7,
]

LINES_TO_PROCESS = 100

#
# 1. Remove empty lines
# 2. Remove some unwanted strings like internal timestamps, bfc tags
#

for idx, line in enumerate(rawfile):

    # Remove the NULL char '\0' at the first line if it exists
    if idx == 0 and line[0] == '\0':
        continue
    # Remove empty line
    if line in ['\n', '\r\n']:
        continue

    # Remove some unwanted strings
    for pattern in strPatterns:
        line = pattern.sub('', line, count=1)

    normfile.write(line)

    # Check only part of lines which are usually enough to determine timestamp
    if idx >= LINES_TO_PROCESS:
        break

rawfile.close()
normfile.close()