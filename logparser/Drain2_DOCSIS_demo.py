#!/usr/bin/env python3
"""
Description : This file does regrex, paramter settings and then calls the parsing core
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
from Drain2 import Para, Drain

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

"""
Input and output files
"""
# Read the config file to decide if train or test data to be processed
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conline = confile.readline().strip()
    if conline == 'TRAINING=1':
        TRAINING = True
    else:
        TRAINING = False

if TRAINING:
    log_file_name = 'train_norm.txt'
    results_loc = '/results/train/'
else:
    log_file_name = 'test_norm.txt'
    results_loc = '/results/test/'

input_dir   = parentdir + '/logs/'              # The input directory of log file
output_dir  = parentdir + results_loc           # The output directory of parsing results
persist_dir = parentdir + '/results/persist/'   # The directory of saving persist files
log_file    = log_file_name                     # The input log file name
log_format  = '<Time> <Content>'                # DOCSIS log format
templatelib = 'template_lib.csv'                # The template lib file name

# Create results/ and sub-dir train/ and test/ if not exist
if not os.path.exists(parentdir+'/results'):
    os.mkdir(parentdir+'/results')

if not os.path.exists(output_dir):
    os.mkdir(output_dir)

"""
Regular expression dict for optional preprocessing (can be empty {})
"""
# The libc ctime format
regexPattern0 = re.compile(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (([0-2]\d)|(3[0-1])) (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{4}')
# MAC Address
regexPattern1 = re.compile(r'([A-Fa-f0-9]+\:){5}[A-Fa-f0-9]+')
# IPv4 Address
regexPattern2 = re.compile(r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)')
# IPv6 Address from https://gist.github.com/mnordhoff/2213179
# A more elegant rex can be found at https://gist.github.com/dfee/6ed3a4b05cfe7a6faf40a2102408d5d8
regexPattern3 = re.compile(r' (?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)(/\d{1,3})?')
# List of intergers and tuples like xxx = 1 2 3 4, (12-11.1) (10-11) as well as Numbers including hex, decimal and integer
regexPattern4 = re.compile(r'( \( \d+\.?(\d+)?-\d+\.?(\d+)? \))+|( \d+){2,}|0x[A-Fa-f0-9]+|(?<=[^A-Za-z0-9])(\-?\+?\d+\.?(\d+)?\*?)')
# OFDM channels CH32 and CH33, maybe different for 3391 and later
regexPattern5 = re.compile(r'CH\d{2}')
regexPattern6 = re.compile(r'\( k[A-Z]\w+ \)|\( [du]cid \)|\( ErrorRecovery \)|\( ConsoleCmdOverride \)|\( T4NoStationMaintTimeout \)|\( T2NoInitMaintTimeout \)')
regexPattern7 = re.compile(r'(QAM lock failure)|(FEC lock failure)')
regexPattern8 = re.compile(r'Stat= (Continue|Success|Abort)')
regexPattern9 = re.compile(r'qam [yn] fec [yn] snr')
regexPattern10 = re.compile(r'txdata [yn]')

regex = {
    regexPattern0: '<*>',
    regexPattern1: '<*>',
    regexPattern2: '<*>',
    regexPattern3: '<*>',
    regexPattern4: ' <*>',
    regexPattern5: '<*>',
    regexPattern6: '( <*> )',
    regexPattern7: '<*>',
    regexPattern8: 'Stat= <*>',
    regexPattern9: 'qam <*> fec <*> snr',
    regexPattern10: 'txdata <*>',
}


"""
Regular expression list for special tokens
"""
sTokenPattern0 = re.compile(r'[a-zA-Z]+[0-9]*[a-zA-Z]*\:')
sTokenPattern1 = re.compile(r'[a-zA-Z]+\=')

sTokenPatterns = [
    sTokenPattern0,
    sTokenPattern1
]

myPara = Para(log_format, log_file, templatelib, indir=input_dir, outdir=output_dir, \
              pstdir=persist_dir, rex=regex, rex_s_token=sTokenPatterns)

myParser = Drain(myPara)
myParser.mainProcess()