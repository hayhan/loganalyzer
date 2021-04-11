#!/usr/bin/env python3
"""
Description : This file does regrex, paramter settings and then calls the parsing core
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import sys

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
sys.path.append(parentdir)

from drain2 import Para, Drain

#
# Input and output files
#

# Read the config file to decide if train or test data to be processed
with open(grandpadir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    TRAINING = bool(conlines[0].strip() == 'TRAINING=1')
    METRICSEN = bool(conlines[1].strip() == 'METRICS=1')
    DLOGCONTEXT = bool(conlines[2].strip() == 'MODEL=DEEPLOG')
    OSSCONTEXT = bool(conlines[2].strip() == 'MODEL=OSS')

if TRAINING:
    LOG_FILE = 'train_norm.txt'
    output_dir = grandpadir + '/results/train/'
else:
    LOG_FILE = 'test_norm.txt'
    output_dir = grandpadir + '/results/test/'

input_dir = grandpadir + '/logs/cm/'            # The input directory of log file
persist_dir = grandpadir + '/results/persist/'  # The directory of saving persist files
TEMPLATE_LIB = 'template_lib.csv'               # The template lib file name
LOG_FORMAT = '<Time> <Content>'                 # DOCSIS log format

# For DeepLog predict and OSS, check the runtime RESERVE_TS to see if there are
# timestamps in the norm log file
if (DLOGCONTEXT or OSSCONTEXT) and ((not TRAINING) and (not METRICSEN)):
    with open(grandpadir+'/results/test/test_runtime_para.txt', 'r') as parafile:
        paralines = parafile.readlines()
        RESERVE_TS = bool(paralines[0].strip() == 'RESERVE_TS=1')
    if not RESERVE_TS:
        LOG_FORMAT = '<Content>'                # DOCSIS log format

# Create results/ and sub-dir train/ and test/ if not exist
if not os.path.exists(grandpadir+'/results'):
    os.mkdir(grandpadir+'/results')

if not os.path.exists(output_dir):
    os.mkdir(output_dir)

if not os.path.exists(persist_dir):
    os.mkdir(persist_dir)

#
# Regular expression dict for optional preprocessing (can be empty {})
#

# The libc ctime format
regexPattern0 = re.compile(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) '
                           r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) '
                           r'(([0-2]\d)|(3[0-1])) '
                           r'(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{4}')

# SNMP MIB OID
regexPattern1 = re.compile(r'([0-9]+\.){4,20}[0-9]+')

# MAC Address
regexPattern2 = re.compile(r'([A-Fa-f0-9]+\:){5}[A-Fa-f0-9]+')

# IPv4 Address
regexPattern3 = re.compile(r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)')

# IPv6 Address from https://gist.github.com/mnordhoff/2213179
# A more elegant rex can be found at
# https://gist.github.com/dfee/6ed3a4b05cfe7a6faf40a2102408d5d8
regexPattern4 = re.compile(r' (?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}'
                           r'|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]'
                           r'|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
                           r'|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}'
                           r'|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]'
                           r'|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
                           r'|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}'
                           r'(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}'
                           r'|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]'
                           r'|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]'
                           r'{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]'
                           r'|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}'
                           r'|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]'
                           r'{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}'
                           r'|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]'
                           r'|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:)'
                           r'{,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:'
                           r'[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]'
                           r'|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
                           r'|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]'
                           r'{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]'
                           r'|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
                           r'|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}'
                           r'|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)(/\d{1,3})?')

# The filename string of image
regexPattern5 = re.compile(r'(?<= Filename: )\S+')

# List of intergers and tuples like xxx = 1 2 3 4, (12-11.1) (10-11) as well as Numbers
# including hex, decimal and integer
regexPattern6 = re.compile(r'(?<=value=)(( [a-f0-9]{2}){14})'
                           r'|(?<=HEX:)([A-F0-9]{2} )+'
                           r'|( \( \d+\.?(\d+)?-\d+\.?(\d+)? \))+|( \d+){2,}|0x[A-Fa-f0-9]+'
                           r'|(?<=[^A-Za-z0-9\.])(\-?\+?\d+\.?(\d+)?\*?)|(?<=\.\.)(\d+)')

# OFDM channels CH32 and CH33, maybe different for 3391 and later
regexPattern7 = re.compile(r'CH\d{2}')

regexPattern8 = re.compile(r'\( k[A-Z]\w+ \)|\( [du]cid \)|\( ErrorRecovery \)'
                           r'|\( ConsoleCmdOverride \)|\( T4NoStationMaintTimeout \)'
                           r'|\( T2NoInitMaintTimeout \)|\( not specified \)')

regexPattern9 = re.compile(r'(QAM lock failure)|(FEC lock failure)')
regexPattern10 = re.compile(r'Stat= (Continue|Success|Abort)')
regexPattern11 = re.compile(r'qam [yn] fec [yn] snr')
regexPattern12 = re.compile(r'txdata [yn]')

regex = {
    regexPattern0: '<*>',
    regexPattern1: '<*>',
    regexPattern2: '<*>',
    regexPattern3: '<*>',
    regexPattern4: ' <*>',
    regexPattern5: '<*>',
    regexPattern6: ' <*>',
    regexPattern7: '<*>',
    regexPattern8: '( <*> )',
    regexPattern9: '<*>',
    regexPattern10: 'Stat= <*>',
    regexPattern11: 'qam <*> fec <*> snr',
    regexPattern12: 'txdata <*>',
}


#
# Regular expression list for special tokens, I want the special tokens are
# same between the template and the accepted log at the corresponding offset
#
sTokenPattern0 = re.compile(r'[a-zA-Z]+[0-9]*[a-zA-Z]*\:')
sTokenPattern1 = re.compile(r'[a-zA-Z]+\=')
sTokenPattern2 = re.compile(r'\(')
sTokenPattern3 = re.compile(r'\)')

sTokenPatterns = [
    sTokenPattern0,
    sTokenPattern1,
    sTokenPattern2,
    sTokenPattern3,
]

myPara = Para(LOG_FORMAT, LOG_FILE, TEMPLATE_LIB, indir=input_dir, outdir=output_dir, \
              pstdir=persist_dir, rex=regex, rex_s_token=sTokenPatterns, incUpdate=1, \
              overWrLib=TRAINING, prnTree=0, nopgbar=0)

myParser = Drain(myPara)
myParser.mainProcess()
