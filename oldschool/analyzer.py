"""
Description : Use the old way to analyze each log (line) by searching in a local database
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
#import sys
#import re
import pickle
import pandas as pd
from tqdm import tqdm
import knowledgebase_cm as kb

# Absolute path of current file
curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
#sys.path.append(parentdir)

#from tools import helper

# The norm file -> test file line mapping
rawln_idx_file = parentdir + '/results/test/rawline_idx_norm.pkl'

# Load the norm structured log file, which is the result of log parser module
structured_file = parentdir+'/results/test/test_norm.txt_structured.csv'

# Read the runtime parameters
with open(parentdir+'/results/test/test_runtime_para.txt', 'r') as parafile:
    paralines = parafile.readlines()
    RESERVE_TS = bool(paralines[0].strip() == 'RESERVE_TS=1')

# Check what we use for each log, timestamp or linenum
if RESERVE_TS:
    columns = ['Time', 'Content', 'EventTemplate', 'EventId']
else:
    columns = ['Content', 'EventTemplate', 'EventId']

data_df = pd.read_csv(structured_file, usecols=columns)
logsize = data_df.shape[0]

# Output file that stores the summary results
sum_file = parentdir+'/results/test/analysis_summary.csv'


if __name__ == '__main__':
    # Init some values for storing analysis results for each detected fault log/line
    log_desc_l = []
    log_sugg_l = []
    log_time_l = []
    summary_df = pd.DataFrame()

    print("Oldschool way to analyze:")
    # Init progress bar to 0%
    #helper.printProgressBar(0, logsize, prefix ='Progress:', suffix='Complete')
    # A lower overhead progress bar
    pbar = tqdm(total=logsize, unit='Logs', disable=False,
                bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

    for _rowIndex, line in data_df.iterrows():
        log_content_l = line['Content'].strip().split()
        log_event_template_l = line['EventTemplate'].strip().split()
        event_id = line['EventId']

        # Update the progress bar
        #helper.printProgressBar(_rowIndex+1, logsize, prefix='Progress:', suffix ='Complete')
        pbar.update(1)

        if len(log_content_l) != len(log_event_template_l):
            continue

        # Traverse all <*> tokens in log_event_template_l and save the index
        # Consider cases like '<*>;', '<*>,', etc. Remove the unwanted ';,' in knowledgebase
        idx_list = [idx for idx, value in enumerate(log_event_template_l) if '<*>' in value]
        #print(idx_list)
        param_list = [log_content_l[idx] for idx in idx_list]
        #print(param_list)

        # Now we can search in the knowledge base for the current log
        log_fault, log_desc, log_sugg = kb.domain_knowledge(event_id, param_list)

        # If current log is fault, store the timestamp, log descrition and suggestion to lists
        if log_fault:
            # Check if the timestamps are in the logs
            if RESERVE_TS:
                time_stamp = line['Time']
            else:
                # Use the line number to replace timestamp in original test.txt
                # _rowIndex is the line number (0-based) in norm/norm structured file

                # Load the line mapping list between raw and norm test file
                with open(rawln_idx_file, 'rb') as f:
                    raw_idx_vector_norm = pickle.load(f)

                # Retrive the line number (1-based) in the test file
                time_stamp = raw_idx_vector_norm[_rowIndex]

            # Store the info of each anomaly log
            log_time_l.append(time_stamp)
            log_desc_l.append(log_desc)
            log_sugg_l.append(log_sugg)

    # Close the progress bar
    pbar.close()
    # Store the results to data frame and file
    summary_df['Time/LineNum'] = log_time_l
    summary_df['Description'] = log_desc_l
    summary_df['Suggestion'] = log_sugg_l
    #print(summary_df)

    # Save the summary data frame to file
    summary_df.to_csv(sum_file, index=False, columns=["Time/LineNum", "Description", "Suggestion"])
