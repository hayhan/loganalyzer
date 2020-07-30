"""
Description : Concatenate multiple text files into one
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import shutil

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

with open(raw_out_file, 'w') as rawout:
    for rf in raw_in_lst:
        # Remove the utf-8 BOM in case it exists
        with open(rf, 'r', encoding='utf-8-sig') as rawin:
            shutil.copyfileobj(rawin, rawout)
            # Add newline in case there is no one at the end of the preceding file
            rawout.write('\n')

#--block comment out start--
#with open(raw_out_file, 'w') as rawout:
#    for rf in raw_in_lst:
#        with open(rf, 'r', encoding='utf-8-sig') as rawin:
#            for line in rawin:
#                rawout.write(line)
#            rawout.write('\n')
#--end--
