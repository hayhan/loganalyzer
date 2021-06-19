"""
Description : Concatenate multiple log files into big one
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import re
import shutil

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

#------------------------------------------------------------------------------------
# Script parameters:
# sys.argv[0]: script name
# sys.argv[1]: raw input files location, e.g. logs/raw/LOG_TYPE or logs/LOG_TYPE
# sys.argv[2]: optional. The raw input file list. The format: file1/file2/.../fileN
#
# If sys.argv[2] exists, cat the files in the list. If does not exist, cat the files
# under the directory sys.argv[1] (including all sub-dir)
#
# The output file is either train.txt or text.txt, depending on the config file
#------------------------------------------------------------------------------------

with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')
    TRAINING = bool(conlines[1].strip() == 'TRAINING=1')
    MODEL = conlines[3].strip().replace('MODEL=', '')

if TRAINING:
    O_NAME = '/train.txt'
else:
    O_NAME = '/test.txt'

raw_dir = parentdir + '/' + sys.argv[1]
monolith_out = open(parentdir + '/logs/' + LOG_TYPE + O_NAME, 'w', encoding='utf-8')

#------------------------------------------------------------------------------------
# Cat the files in the file list which is provided in the command parameters
#------------------------------------------------------------------------------------
if len(sys.argv) == 3:
    # Parse the raw input file list string file1/file2/.../fileN
    # Result is a list in which the element is raw_in_loc+file(i) where i= 1, 2, ..., n
    raw_in_lst = []
    raw_in_lst_str = sys.argv[2]
    t_lst = raw_in_lst_str.split(sep='/')
    for rf in t_lst:
        raw_in_lst.append(raw_dir + '/' + rf)

    for rf in raw_in_lst:
        # Remove the utf-8 BOM in case it exists
        with open(rf, 'r', encoding='utf-8-sig') as rawin:
            shutil.copyfileobj(rawin, monolith_out)
            # Add newline in case there is no one at the end of the preceding file
            monolith_out.write('\n')

    monolith_out.close()
    sys.exit()

#------------------------------------------------------------------------------------
# Cat the files under provided directory (including sub directories)
#------------------------------------------------------------------------------------

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738].
pattern_timestamp = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
                               r'\.(\d{3})|24:00:00\.000)\] (abn: )?')

# Skip file list
skip_list = ['readme.txt', 'desc.txt']

# This is used for DeepLog training and validation by considering session labels
if MODEL == 'DEEPLOG':
    for dirpath, dirnames, files in sorted(os.walk(raw_dir, topdown=True)):
        # print(f'Found directory: {dirpath}')
        for filename in files:
            if filename in skip_list:
                continue
            rf = os.path.join(dirpath, filename)
            #print(rf)
            with open(rf, 'r', encoding='utf-8-sig') as rawin:
                for idx, line in enumerate(rawin):
                    # Insert 'segsign: ' to the start line of each file
                    if idx == 0:
                        matchTS = pattern_timestamp.match(line)
                        if matchTS:
                            currentLineTS = matchTS.group(0)
                            newline = pattern_timestamp.sub('', line, count=1)
                            line = currentLineTS + 'segsign: ' + newline
                        else:
                            print("Error: The timestamp is wrong!")
                    monolith_out.write(line)
                monolith_out.write('\n')

# This is used for template generation / update and detector
elif MODEL in ['TEMPUPDT', 'DETECTOR']:
    for dirpath, dirnames, files in sorted(os.walk(raw_dir, topdown=True)):
        # print(f'Found directory: {dirpath}')
        for filename in files:
            if filename in skip_list:
                continue
            rf = os.path.join(dirpath, filename)
            #print(rf)
            with open(rf, 'r', encoding='utf-8-sig') as rawin:
                shutil.copyfileobj(rawin, monolith_out)
                # Add newline in case there is no one at the end of the preceding file
                monolith_out.write('\n')

# This is used for Loglab multi-classification training. Also can be used for template
# update under logs/raw/LOG_TYPE/loglab/
elif MODEL[0:6] == 'LOGLAB':
    # The pattern for class name of loglab
    pattern_classname = re.compile(r'c[0-9]{3}')
    loglab_dir = parentdir + '/logs/raw/' + LOG_TYPE + '/loglab'

    # Note: name the class folder as 'cxxx', and training log files in it as '*_xxx.txt'
    # Concatenate files under logs/raw/LOG_TYPE/loglab/c001/ ... /cxxx/.
    for dirpath, dirnames, files in sorted(os.walk(loglab_dir, topdown=True)):
        #print(f'Found directory: {dirpath}')
        # Extract the class name (sub-folder name cxxx, dirpath[-4:])
        classname = re.split(r'[\\|/]', dirpath.strip('[\\|/]'))[-1]
        if not pattern_classname.match(classname):
            # Skip loglab itself and non-standard class name sub-folders if any exists
            continue
        # Sort the files per the file name string[-7:-4], aka. the 3 digits num part
        for filename in sorted(files, key=lambda x:x[-7:-4]):
            rf = os.path.join(dirpath, filename)
            #print(rf)
            with open(rf, 'r', encoding='utf-8-sig') as rawin:
                for idx, line in enumerate(rawin):
                    # Insert class_name to the start line of each file
                    if idx == 0:
                        match = pattern_timestamp.match(line)
                        if match:
                            curline_ts = match.group(0)
                            newline = pattern_timestamp.sub('', line, count=1)
                            line = curline_ts + classname + ' ' + newline
                        else:
                            print("Error: The timestamp is wrong!")
                    monolith_out.write(line)
                monolith_out.write('\n')

else:
    print("Error: Check the MODEL value in config file!")

monolith_out.close()
