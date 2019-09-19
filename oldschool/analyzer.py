"""
Description : Use the old way to analyze each log (line) by searching in a local database 
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import pandas as pd
import knowledgebase as kb

# Print progress bar at https://gist.github.com/greenstick/b23e475d2bfdc3a82e34eaa1f6781ee4
def printProgressBar (iteration, total, prefix='', suffix='', decimals=1, length=100, fill='|'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end ='\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

# Absolute path of current file
curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

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
    printProgressBar(0, logsize, prefix ='Progress:', suffix='Complete', length=50)

    for rowIndex, line in data_df.iterrows():
        timeStamp = line['Time']
        logContentL = line['Content'].strip().split()
        logEventTemplateL = line['EventTemplate'].strip().split()
        eventId = line['EventId']

        # Update the progress bar
        printProgressBar(rowIndex+1, logsize, prefix='Progress:', suffix ='Complete', length=50)

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

    # Store the results to data frame and file
    summary_df['Time'] = logTimeL
    summary_df['Description'] = logDescL
    summary_df['Suggestion'] = logSuggL
    #print(summary_df)

    # Save the summary data frame to file
    summary_df.to_csv(summary_file, index=False, columns=["Time", "Description", "Suggestion"])