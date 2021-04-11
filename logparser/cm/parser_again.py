#!/usr/bin/env python3
"""
Description : This file does the 2nd time clustering for some cases
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
# Currently this file is ONLY used for DeepLog predict.
# Not for DeepLog train and validation.
# Not for OSS and CML.
# So we no need check some enviroment variables in config.txt
#
input_dir = grandpadir + '/logs/cm/'               # The input directory of log file
output_dir = grandpadir + '/results/test/cm/'      # The output directory of parsing results
persist_dir = grandpadir + '/results/persist/cm/'  # The directory of saving persist files
TEMPLATE_LIB = 'template_lib.csv'                  # The template lib file name
LOG_FILE = 'test_norm_pred.txt'                    # The input log file name
LOG_FORMAT = '<Time> <Content>'                    # DOCSIS log format

# Check the runtime value of RESERVE_TS to see if there are timestamps
with open(grandpadir+'/results/test/cm/test_runtime_para.txt', 'r') as parafile:
    paralines = parafile.readlines()
    RESERVE_TS = bool(paralines[0].strip() == 'RESERVE_TS=1')
if not RESERVE_TS:
    LOG_FORMAT = '<Content>'                       # DOCSIS log format

#
# Regular expression dict for optional preprocessing (can be empty {})
#
regex = {
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

myPara = Para(LOG_FORMAT, LOG_FILE, TEMPLATE_LIB, indir=input_dir, outdir=output_dir,
              pstdir=persist_dir, rex=regex, rex_s_token=sTokenPatterns, incUpdate=1,
              overWrLib=False, prnTree=0, nopgbar=0)

myParser = Drain(myPara)
myParser.mainProcess()
