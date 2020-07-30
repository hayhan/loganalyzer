"""
Description : Concatenate multiple text files into one with segment signs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import re

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

#--------------------------------------------------------------------
# Script parameters:
# sys.argv[0]: script name
# sys.argv[1]: raw input files location, e.g. logs/raw
# sys.argv[2]: raw input file list. The format: file1/file2/.../fileN
# sys.argv[3]: raw output file location and name, e.g. logs/train.txt
#--------------------------------------------------------------------

raw_in_loc = parentdir + '/' + sys.argv[1]
raw_out_file = parentdir + '/' + sys.argv[3]
raw_in_lst_str = sys.argv[2]

# Parse the raw input file list string file1/file2/.../fileN
# Result is a list in which the element is raw_in_loc+file(i) where i= 1, 2, ..., n
raw_in_lst = []
t_lst = raw_in_lst_str.split(sep='/')
for rf in t_lst:
    raw_in_lst.append(raw_in_loc + '/' + rf)

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738].
#
strPattern0 = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
                         r'\.(\d{3})|24:00:00\.000)\] ')

with open(raw_out_file, 'w') as rawout:
    for rf in raw_in_lst:
        with open(rf, 'r', encoding='utf-8-sig') as rawin:
            for idx, line in enumerate(rawin):
                # Insert 'segsign: ' to the start line of each segment from each file
                if idx == 0:
                    matchTS = strPattern0.match(line)
                    if matchTS:
                        currentLineTS = matchTS.group(0)
                        newline = strPattern0.sub('', line, count=1)
                        line = currentLineTS + 'segsign: ' + newline
                    else:
                        print("Error: The timestamp is wrong!")
                rawout.write(line)
            rawout.write('\n')
