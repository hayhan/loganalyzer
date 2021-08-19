# Licensed under the MIT License - see License.txt
""" The oldschool system package (OSS).
"""
import sys
import logging
import pickle
from typing import List
from importlib import import_module
import pandas as pd
from tqdm import tqdm
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC

# Load knowledge-base of LOG_TYPE
kb = import_module("analyzer.oldschool." + dh.LOG_TYPE + ".knowledgebase")

__all__ = ["OSS"]


log = logging.getLogger(__name__)

class OSS():
    """ The oldshcool class """
    def __init__(self, df_raws, raw_idx_norm):
        self.fzip: dict = dh.get_files_io()
        self.intmdt: bool = GC.conf['general']['intmdt']
        self.aim: bool = GC.conf['general']['aim']
        self._log_head_offset: int = GC.conf['general']['head_offset']
        self._raw_ln_idx_norm: List[int] = raw_idx_norm
        self._df_raws = df_raws
        self._summary_df = pd.DataFrame(
            columns=['Time/LineNum', 'Description', 'Suggestion'])


    def invalid_log_warning(self):
        """ Warning message which is saved into txt file
        """
        print("The submitted log is NOT from {}.".format(dh.LOG_TYPE))

        # Save the warning message to the top summary file
        with open(self.fzip['top'], 'w') as fio:
            fio.write("You sbumitted a wrong log, which is NOT from {}. Please check." \
                    .format(dh.LOG_TYPE))
        # Save empty summary data frame to file
        self._summary_df.to_csv(self.fzip['sum'], index=False,
            columns=["Time/LineNum", "Description", "Suggestion"])


    # pylint: disable=too-many-locals
    def analyze(self):
        """ Search the knowledge-base to analyze the logs """
        # Init some values for each detected fault log/line
        log_desc_l: List[str] = []
        log_sugg_l: List[str] = []
        log_time_l: List[str] = []

        # Check the timestamp width we learned
        if self._log_head_offset < 0:
            # Not LOG_TYPE log defined in config file. Return right now.
            self.invalid_log_warning()
            sys.exit(1)

        # Use in-memory data by default unless config file tells
        if not GC.conf['general']['aim']:
            self._df_raws = pd.read_csv(self.fzip['structured'])
            with open(self.fzip['rawln_idx'], 'rb') as fin:
                self._raw_ln_idx_norm = pickle.load(fin)

        # A lower overhead progress bar
        pbar = tqdm(total=self._df_raws.shape[0], unit='Logs', disable=False,
                    bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

        for rowidx, line in self._df_raws.iterrows():
            log_content_l = line['Content'].strip().split()
            log_event_tmplt_l = line['EventTemplate'].strip().split()
            event_id = line['EventId']

            pbar.update(1)

            if len(log_content_l) != len(log_event_tmplt_l):
                continue

            # Traverse all <*> tokens in log_event_tmplt_l and save the
            # index. Consider cases like '<*>;', '<*>,', etc. Remove the
            # unwanted ';,' in knowledgebase.
            idx_list = [idx for idx, value in enumerate(log_event_tmplt_l) if '<*>' in value]
            # print(idx_list)
            param_list = [log_content_l[idx] for idx in idx_list]
            # print(param_list)

            # Now we can search in knowledge-base for the current log
            log_fault, \
            log_desc, \
            log_sugg = kb.domain_knowledge(event_id, param_list)

            # If current log is fault, store the timestamp, the log
            # descrition and suggestion
            if log_fault:
                # Check if the timestamps are in the logs
                if self._log_head_offset > 0:
                    time_stamp = line['Time']
                else:
                    # Use line number to replace timestamp in original
                    # test.txt. rowidx is the line number (0-based) in
                    # norm structured data/file

                    # Retrive the line number (1-based) in the test file
                    time_stamp = self._raw_ln_idx_norm[rowidx]

                # Store the info of each anomaly log
                log_time_l.append(time_stamp)
                log_desc_l.append(log_desc)
                log_sugg_l.append(log_sugg)

        pbar.close()
        # Store the results to dataframe and file
        self._summary_df['Time/LineNum'] = log_time_l
        self._summary_df['Description'] = log_desc_l
        self._summary_df['Suggestion'] = log_sugg_l

        # Aggregate summaries and remove duplicates
        summary_top = list(dict.fromkeys(log_sugg_l))

        # Save the top summary to a file
        with open(self.fzip['top'], 'w') as outfile:
            if len(summary_top) > 0:
                for idx, item in enumerate(summary_top):
                    outfile.write(str(idx+1) + ') ' + item)
                    outfile.write('\n')
            else:
                outfile.write("Oops, the wrong logs are not in the knowledge-base. \
                               Feed Back Please by clicking the link above.")

        # Save the summary data frame to file
        self._summary_df.to_csv(self.fzip['sum'], index=False,
            columns=["Time/LineNum", "Description", "Suggestion"])
