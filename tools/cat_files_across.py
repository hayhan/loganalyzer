"""
Description : Concatenate multiple text files into one across directories for loglab
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')

loglab_dir = parentdir + '/logs/raw/' + LOG_TYPE + '/loglab'
monolith_out = open(parentdir + '/logs/' + LOG_TYPE + '/train.txt', 'w', encoding='utf-8')

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738].
pattern_timestamp = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
                               r'\.(\d{3})|24:00:00\.000)\] ')
# The pattern for class name of loglab
pattern_classname = re.compile(r'c[0-9]{3}')

# Note: name the class folder as 'cxxx', and training log files in it as '*_xxx.txt'
# Concatenate files under logs/raw/LOG_TYPE/loglab/c001/ ... /cxxx/.
for dirpath, dirnames, files in sorted(os.walk(loglab_dir, topdown=True)):
    print(f'Found directory: {dirpath}')
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

monolith_out.close()
