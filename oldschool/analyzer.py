#!/usr/bin/env python3
"""
Description : Use the old way to analyze each log (line) by searching a local database 
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import pandas as pd
#from paramextor import param_extractor

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

structured_file = parentdir+'/results/test/test_norm.txt_structured.test.csv'

data_df = pd.read_csv(structured_file, usecols=['Content', 'EventTemplate', 'EventId'])

for index, line in data_df.iterrows():
    logContentL = line['Content'].strip().split()
    logEventTemplateL = line['EventTemplate'].strip().split()
    eventId = line['EventId']

    if len(logContentL) != len(logEventTemplateL):
        continue

    print(logContentL)
    print(logEventTemplateL)
    print(eventId)

    # Traverse all <*> tokens in logEventTemplateL and save the index
    # ToDo: Need consider other cases like '<*>;', '<*>,', etc
    idx_list = [idx for idx, value in enumerate(logEventTemplateL) if value == '<*>']
    print(idx_list)
    param_list = [logContentL[idx] for idx in idx_list]
    print(param_list)

    # Now we can search the knowledge base for the current log