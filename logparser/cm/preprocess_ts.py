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

with open(grandpadir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    TRAINING = bool(conlines[1].strip() == 'TRAINING=1')
    METRICSEN = bool(conlines[2].strip() == 'METRICS=1')
    DLOGCONTEXT = bool(conlines[3].strip() == 'MODEL=DEEPLOG')
    OSSCONTEXT = bool(conlines[3].strip() == 'MODEL=OSS')
    LLABCONTEXT = bool(conlines[3].strip()[0:12] == 'MODEL=LOGLAB')

raw_file_loc = grandpadir + '/logs/cm/test.txt'
norm_file_loc = grandpadir + '/logs/cm/test_norm.txt'
runtime_para_loc = grandpadir + '/results/test/cm/test_runtime_para.txt'

rawfile = open(raw_file_loc, 'r', encoding='utf-8-sig')
normfile = open(norm_file_loc, 'w', encoding='utf-8')

#----------------------------------------------------------------------------------------
# Patterns for removing non-primary timestamp, console prompt and others
#----------------------------------------------------------------------------------------
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

#----------------------------------------------------------------------------------------
# Patterns for other specific lines
#----------------------------------------------------------------------------------------
# Assign token something like ABC=xyz or ABC==xyz
assignTokenPattern = re.compile(r'=(?=[^= \r\n])')
# Cpp class token like ABC::Xyz or ABC::xY
cppClassPattern = re.compile(r'\:\:(?=[A-Z][a-z0-9]|[a-z][A-Z])')
# Split 'ABC;DEF' to 'ABC; DEF'
semicolonPattern = re.compile(r';(?! )')
# Change something like (xx), [xx], ..., to ( xx ), [ xx ], ...
bracketPattern1 = re.compile(r'\((?=(\w|[-+]))')
bracketPattern2 = re.compile(r'(?<=\w)\)')
bracketPattern3 = re.compile(r'\[(?=(\w|[-+]))')
bracketPattern4 = re.compile(r'(?<=\w)\]')
bracketPattern5 = re.compile(r'\d+(?=(ms))')

LINES_TO_PROCESS = 500

#
# 1. Remove empty lines
# 2. Remove some unwanted strings like internal timestamps, bfc tags
#

for idx, line in enumerate(rawfile):

    # Remove the NULL char '\0' at the first line if it exists
    if idx == 0 and line[0] == '\0':
        continue

    # Remove some unwanted strings
    for pattern in strPatterns:
        line = pattern.sub('', line, count=1)

    # Remove empty line
    if line in ['\n', '\r\n']:
        continue

    # Split assignment token something like ABC=xyz to ABC= xyz
    line = assignTokenPattern.sub('= ', line)

    # Split class token like ABC::Xyz: to ABC:: Xyz:
    line = cppClassPattern.sub(':: ', line)

    # Split 'ABC;DEF' to 'ABC; DEF'
    line = semicolonPattern.sub('; ', line)

    # Change something like (xx), [xx], ..., to ( xx ), [ xx ], ...
    line = bracketPattern1.sub('( ', line)
    line = bracketPattern2.sub(' )', line)
    #line = bracketPattern3.sub('[ ', line)
    #line = bracketPattern4.sub(' ]', line)

    m = bracketPattern5.search(line)
    if m:
        substring = m.group(0)
        line = bracketPattern5.sub(substring+' ', line)

    normfile.write(line)

    # Check only part of lines which are usually enough to determine timestamp
    if idx >= LINES_TO_PROCESS:
        break

rawfile.close()
normfile.close()

# Suppose no timestamps in the log file before we detect them
# Do it only for prediction in DeepLog/Loglab and OSS
if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)):
    with open(runtime_para_loc, 'w') as f:
        f.write('RESERVE_TS=0')
