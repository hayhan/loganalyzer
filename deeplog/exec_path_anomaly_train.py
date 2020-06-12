#!/usr/bin/env python3
"""
Description : Train the DeepLog model for execution path anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
sys.path.append(parentdir)

# Read parameters from the config file
with open(parentdir+'/entrance/deeplog_config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    # Metrics enable
    metricsEn = bool(conlines[1].strip() == 'METRICS=1')
    # Read the sliding window size
    WINDOW_SIZE = int(conlines[3].strip().replace('WINDOW_SIZE=', ''))
    # Read the sliding window step size
    WINDOW_STEP = int(conlines[4].strip().replace('WINDOW_STEP=', ''))
    # Read the template library size
    TEMPLATE_LIB_SIZE = int(conlines[5].strip().replace('TEMPLATE_LIB_SIZE=', ''))


if __name__ == '__main__':
    print("===> Start training the execution path model ...")
    