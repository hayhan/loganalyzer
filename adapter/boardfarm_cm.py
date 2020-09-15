#!/usr/bin/env python3
"""
Description : This file adapts CM log from boardfarm system to the preprocessor
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

#
# The raw boardfarm log should be processed by following command to remove ^M charactors
# sed -e "s/\r//g" cm_console.log > test_boardfarm.txt
#
raw_file_loc = parentdir + '/logs/test_boardfarm.txt'
new_file_loc = parentdir + '/logs/test.txt'

rawfile = open(raw_file_loc, 'r', encoding='utf-8-sig')
newfile = open(new_file_loc, 'w')

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738].
pattern_ts = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
                        r'\.(\d{3})|24:00:00\.000)\] ')
# The pattern for the abnormal timestamp from boardfarm system, e.g. [ 1650]
pattern_abn_ts = re.compile(r' \[ *\d+\]')
# The pattern for CM console prompts
pattern_pt = re.compile('CM> ')

#
# We do followings to adapt the boardfarm log to existing pre-processor of log parser
# 1. Remove the abnormal timestamp with the main timestamp
# 2. Add the main timestamp if both main and abnormal timestamps do not exist
# 3. Remove the prompt 'CM> ', which might be anywhere in the line
#

curline_ts = '[19700101-00:00:00.000] '

for idx, line in enumerate(rawfile):

    # Remove the NULL char '\0' at the first line if it exists
    if idx == 0:
        line[0] == '\0'
        continue

    # Save the main timestamp if it exists. The newline does not contain the main
    # timestamp before write it back to a new file. Add it back at the end.
    match_ts = pattern_ts.match(line)
    if match_ts:
        # Match the main timestamp
        curline_ts = match_ts.group(0)
        newline = pattern_ts.sub('', line, count=1)
    else:
        match_abn_ts = pattern_abn_ts.match(line)
        if match_abn_ts:
            # Match the abnormal timestamp from boardfarm system
            newline = pattern_abn_ts.sub('', line, count=1)
        else:
            # It means both main timestamp and abnormal timestamp do not exist
            newline = line

    # Remove console prompt
    if pattern_pt.search(newline):
        newline = pattern_pt.sub('', newline)

    # Write current line to a new file with the timestamp
    newline = curline_ts + newline
    newfile.write(newline)

rawfile.close()
newfile.close()
