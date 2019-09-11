#!/usr/bin/env python3
"""
Description : Use the old way to analyze each log (line) by searching in a local database 
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import pandas as pd
import knowledgebase as kb

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

# Load the norm structured log file, which is the result of log parser module
structured_file = parentdir+'/results/test/test_norm.txt_structured.csv'
data_df = pd.read_csv(structured_file, usecols=['Time', 'Content', 'EventTemplate', 'EventId'])

# Output file that stores the summary results
summary_file = parentdir+'/results/test/analysis_summary.csv'

# Init some values for storing analysis results for each detected fault log/line
logDescL = []
logSuggL = []
logTimeL = []
summary_df = pd.DataFrame()

for rowIndex, line in data_df.iterrows():
    timeStamp = line['Time']
    logContentL = line['Content'].strip().split()
    logEventTemplateL = line['EventTemplate'].strip().split()
    eventId = line['EventId']

    if len(logContentL) != len(logEventTemplateL):
        continue

    # Traverse all <*> tokens in logEventTemplateL and save the index
    # ToDo: consider other cases like '<*>;', '<*>,', etc
    idx_list = [idx for idx, value in enumerate(logEventTemplateL) if value == '<*>']
    #print(idx_list)
    param_list = [logContentL[idx] for idx in idx_list]
    #print(param_list)

    # Now we can search in the knowledge base for the current log
    logFault, logDesc, logSugg = kb.domain_knowledge(eventId, param_list)

    # If current log is fault, store the timestamp, log descrition and suggestion to lists
    if logFault == True:
        logTimeL.append(timeStamp)
        logDescL.append(logDesc)
        logSuggL.append(logSugg)

# Store the results to data frame and file
summary_df['Time'] = logTimeL
summary_df['Description'] = logDescL
summary_df['Suggestion'] = logSuggL
#print(summary_df)

# Save the summary data frame to file
summary_df.to_csv(summary_file, index=False, columns=["Time", "Description", "Suggestion"])