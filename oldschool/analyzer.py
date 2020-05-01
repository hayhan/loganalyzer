"""
Description : Use the old way to analyze each log (line) by searching in a local database 
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
import re
import pandas as pd
import knowledgebase_cm as kb
from tqdm import tqdm

# Absolute path of current file
curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
#sys.path.append(parentdir)

#from tools import helper

# Load the norm structured log file, which is the result of log parser module
structured_file = parentdir+'/results/test/test_norm.txt_structured.csv'
data_df = pd.read_csv(structured_file, usecols=['Time', 'Content', 'EventTemplate', 'EventId'])
logsize = data_df.shape[0]

# Output file that stores the summary results
summary_file = parentdir+'/results/test/analysis_summary.csv'


if __name__ == '__main__':
    # Init some values for storing analysis results for each detected fault log/line
    logDescL = []
    logSuggL = []
    logTimeL = []
    summary_df = pd.DataFrame()

    print("Oldschool way to analyze:")
    # Init progress bar to 0%
    #helper.printProgressBar(0, logsize, prefix ='Progress:', suffix='Complete', length=50)
    # A lower overhead progress bar
    pbar = tqdm(total=logsize, unit='Logs', ncols=100, disable=False)

    for _rowIndex, line in data_df.iterrows():
        timeStamp = line['Time']
        logContentL = line['Content'].strip().split()
        logEventTemplateL = line['EventTemplate'].strip().split()
        eventId = line['EventId']

        # Update the progress bar
        #helper.printProgressBar(_rowIndex+1, logsize, prefix='Progress:', suffix ='Complete', length=50)
        pbar.update(1)

        if len(logContentL) != len(logEventTemplateL):
            continue

        # Traverse all <*> tokens in logEventTemplateL and save the index
        # Consider cases like '<*>;', '<*>,', etc. Remove the unwanted ';,' in knowledgebase
        idx_list = [idx for idx, value in enumerate(logEventTemplateL) if '<*>' in value]
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

    # Close the progress bar
    pbar.close()
    # Store the results to data frame and file
    summary_df['Time'] = logTimeL
    summary_df['Description'] = logDescL
    summary_df['Suggestion'] = logSuggL
    #print(summary_df)

    # Save the summary data frame to file
    summary_df.to_csv(summary_file, index=False, columns=["Time", "Description", "Suggestion"])
