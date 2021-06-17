"""
Description : Normalize the timestamps into the standard format we defined
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

# Iterate each file under logs/raw/tmp/, detect the width of old
# timestamp and replace old one with the standard format we defined

import os
import re
import sys
import subprocess
from datetime import datetime
from shutil import copyfile

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')

tmp_dir = parentdir + '/logs/tmp'
work_dir = parentdir + '/logs/' + LOG_TYPE
parser = parentdir + '/logparser'
parser_domain = parentdir + '/logparser/' + LOG_TYPE
runtime_para = parentdir + '/results/test/' + LOG_TYPE + '/test_runtime_para.txt'

# Support sub-folders
for dirpath, dirnames, files in sorted(os.walk(tmp_dir, topdown=True)):
    # print(f'Found directory: {dirpath}')

    # Get the current system time
    dt_timestamp = datetime.now().timestamp()

    for filename in files:
        # Skip hidden files if any exist
        if filename[0] == '.':
            continue

        newfile = 'new_' + filename
        rf = os.path.join(dirpath, filename)
        df = os.path.join(work_dir, 'test.txt')
        nf = os.path.join(dirpath, newfile)
        # print(rf)

        # Copy file to logs/cm/test.txt
        copyfile(rf, df)

        # Learn the width of timestamp in raw log files
        # Use sys.executable instead of 'python' to keep the subprocess in the virtualenv on Windows
        subprocess.run([sys.executable, os.path.join(parser_domain, 'preprocess_ts.py')], check=False)
        subprocess.run([sys.executable, os.path.join(parser_domain, 'parser.py')], check=False)
        subprocess.run([sys.executable, os.path.join(parser, 'det_timestamp.py')], check=False)

        # Read the width of timestamp, aka. log head offset, we just learned
        with open(runtime_para, 'r') as parafile:
            paralines = parafile.readlines()
            log_offset = int(paralines[0].strip().replace('RESERVE_TS=', ''))
            if log_offset < 0:
                print("Warning: It looks file {} is not {} log.".format(filename, LOG_TYPE))
                continue

        # The pattern for detected timestamp, aka. the log head offset
        pattern_timestamp = re.compile(r'.{%d}' % log_offset)

        # Replace the old timestamp (including no timestamp) with the standard format
        with open(rf, 'r', encoding='utf-8-sig') as rawin:
            outf = open(nf, 'w')
            for line in rawin:
                if pattern_timestamp.match(line):
                    #
                    dt_obj = datetime.fromtimestamp(dt_timestamp)
                    dt_format = '[' + dt_obj.strftime("%Y%m%d-%H:%M:%S.%f")[0:21] + '] '
                    # This works even log_offset is zero, aka. no old timestamp
                    newline = pattern_timestamp.sub(dt_format, line, count=1)
                    # Increase 100ms per line
                    dt_timestamp += 0.100000
                else:
                    # Messed lines, skip
                    continue
                outf.write(newline)
            outf.close()
