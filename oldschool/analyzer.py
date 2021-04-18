"""
Description : Use the old way to analyze each log (line) by searching in a local database
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import sys
#import re
import importlib
import pickle
import pandas as pd
from tqdm import tqdm

# Absolute path of current file
curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
#sys.path.append(parentdir)

#from tools import helper

# Read the config file to see what kind of logs we are processing
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()
    LOG_TYPE = conlines[0].strip().replace('LOG_TYPE=', '')

results_test_dir = parentdir + '/results/test/' + LOG_TYPE + '/'

# Import the knowledge base for the corresponding log type
kb = importlib.import_module(LOG_TYPE + '.knowledgebase')

# The norm file -> test file line mapping
rawln_idx_file = results_test_dir + 'rawline_idx_norm.pkl'

# Load the norm structured log file, which is the result of log parser module
structured_file = results_test_dir + 'test_norm.txt_structured.csv'

# Output file that stores the summary results
top_file = results_test_dir + 'analysis_summary_top.txt'
sum_file = results_test_dir + 'analysis_summary.csv'

# Init some values for storing analysis results for each detected fault log/line
log_desc_l = []
log_sugg_l = []
log_time_l = []
summary_df = pd.DataFrame(columns=['Time/LineNum', 'Description', 'Suggestion'])

def invalid_log_warning():
    """ Warning message which is saved into txt file
    """
    print("The submitted log is NOT from {}.".format(LOG_TYPE))

    # Save the warning message to the top summary file
    with open(top_file, 'w') as fio:
        fio.write("You sbumitted a wrong log, which is NOT from {}. Please check." \
                  .format(LOG_TYPE))

    # Save empty summary data frame to file
    summary_df.to_csv(sum_file, index=False,
                      columns=["Time/LineNum", "Description", "Suggestion"])

# Read the runtime parameters
with open(results_test_dir + 'test_runtime_para.txt', 'r') as parafile:
    paralines = parafile.readlines()
    RESERVE_TS = int(paralines[0].strip().replace('RESERVE_TS=', ''))
if RESERVE_TS < 0:
    # Not LOG_TYPE log. Return right now.
    invalid_log_warning()
    sys.exit(0)

# Check what we use for each log, timestamp or linenum
if RESERVE_TS > 0:
    columns = ['Time', 'Content', 'EventTemplate', 'EventId']
else:
    columns = ['Content', 'EventTemplate', 'EventId']

data_df = pd.read_csv(structured_file, usecols=columns)
logsize = data_df.shape[0]


if __name__ == '__main__':
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
        log_fault, \
        log_desc, \
        log_sugg = kb.domain_knowledge(event_id, param_list)

        # If current log is fault, store the timestamp, log descrition and suggestion
        if log_fault:
            # Check if the timestamps are in the logs
            if RESERVE_TS > 0:
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

    # Aggregate summaries and remove duplicates
    # Add log_evid_l and log_sugg_l element wisely
    #sum_list = [a + b for a, b in zip(log_evid_l, log_sugg_l)]
    #kb.aggregate_summaries(sum_list)
    summary_top = list(dict.fromkeys(log_sugg_l))

    # Save the top summary to a file
    with open(top_file, 'w') as outfile:
        if len(summary_top) > 0:
            for idx, item in enumerate(summary_top):
                outfile.write(str(idx+1) + ') ' + item)
                outfile.write('\n')
        else:
            outfile.write("Oops, the wrong logs are not in the knowledge-base. \
                           Feed Back Please by clicking the link above.")

    # Save the summary data frame to file
    summary_df.to_csv(sum_file, index=False,
                      columns=["Time/LineNum", "Description", "Suggestion"])
