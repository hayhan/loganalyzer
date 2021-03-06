# Licensed under the MIT License - see LICENSE.txt
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
kb = import_module("analyzer.extensions." + dh.LOG_TYPE + ".knowledgebase")


__all__ = ["OSS"]

log = logging.getLogger(__name__)


class OSS():
    """ The oldshcool class """
    def __init__(self, df_raws):
        self.fzip: dict = dh.get_files_io()
        self.aim: bool = GC.conf['general']['aim']
        self._log_head_offset: int = GC.conf['general']['head_offset']
        self._map_norm_raw: List[int] = []
        self._df_raws = df_raws
        self._summary_df = pd.DataFrame(
            columns=["Time/LineNum", "Severity", "Description", "Suggestion"])

        self.kbase = kb.Kb()

    @property
    def map_norm_raw(self):
        """ Get the raw line index in norm data """
        return self._map_norm_raw

    @map_norm_raw.setter
    def map_norm_raw(self, map_norm_raw: List[int]):
        """ Set the raw line index in norm data """
        self._map_norm_raw = map_norm_raw

    def invalid_log_warning(self):
        """ Warning message which is saved into txt file
        """
        print(f"The submitted log is NOT from {dh.LOG_TYPE}.")

        # Save the warning message to the top summary file
        with open(self.fzip['top'], 'w', encoding='utf-8') as fio:
            fio.write(f"You sbumitted logs which are NOT from {dh.LOG_TYPE}.")

        # Save empty summary data frame to file
        self._summary_df.to_csv(self.fzip['sum'], index=False,
            columns=["Time/LineNum", "Severity", "Description", "Suggestion"])

    # pylint: disable=too-many-locals
    def analyze(self):
        """ Search the knowledge-base to analyze the logs """
        # Init some values for each detected fault log/line
        log_desc_l: List[str] = []
        log_sugg_l: List[str] = []
        log_time_l: List[str] = []
        log_seve_l: List[str] = []

        # Bail out early for wrong LOG_TYPE
        if self._log_head_offset < 0:
            self.invalid_log_warning()
            sys.exit(1)

        # Use in-memory data by default unless config tells us to do so.
        if not GC.conf['general']['aim']:
            self._df_raws = pd.read_csv(self.fzip['struct'])
            with open(self.fzip['map_norm_raw'], 'rb') as fin:
                self._map_norm_raw = pickle.load(fin)

        # A lower overhead progress bar
        pbar = tqdm(total=self._df_raws.shape[0], unit='Logs', disable=False,
                    bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

        # Prepare for the iteration. Extract info from dataframe.
        if self._log_head_offset > 0:
            time_logs = self._df_raws['Time'].tolist()
        else:
            time_logs = list(range(self._df_raws.shape[0]))

        eid_logs = self._df_raws['EventId'].tolist()
        tmplt_logs = self._df_raws['EventTemplate'].tolist()
        cont_logs = self._df_raws['Content'].tolist()

        # Do not iterate dataframe using iterrows(). It's very slow.
        for time, eid, tmplt, content in zip(time_logs, eid_logs, tmplt_logs, cont_logs):
            log_content_l = content.strip().split()
            log_tmplt_l = tmplt.strip().split()

            pbar.update(1)

            if len(log_content_l) != len(log_tmplt_l):
                continue

            # Traverse all <*> tokens in log_tmplt_l and save the index.
            # Consider cases like '<*>;', '<*>,', etc. Remove unwanted
            # char ';,' from param in knowledgebase if needed.
            idx_list = [idx for idx, value in enumerate(log_tmplt_l) if '<*>' in value]
            # print(idx_list)
            param_list = [log_content_l[idx] for idx in idx_list]
            # print(param_list)

            # Now we can search in knowledge-base for the current log
            log_seve, _, log_sugg \
                = self.kbase.domain_knowledge(eid, param_list)

            # If current log is fault, store the timestamp, the log
            # descrition and suggestion
            if log_seve != 'info':
                # Check if the timestamps are in the logs
                if self._log_head_offset > 0:
                    time_stamp = time
                else:
                    # Use line number to replace timestamp in original
                    # test.txt. rowidx is the line number (0-based) in
                    # norm structured data/file

                    # Retrive the line number (1-based) in the test file
                    time_stamp = self._map_norm_raw[time]

                # Store the info of each anomaly log
                log_time_l.append(time_stamp)
                log_seve_l.append(log_seve)
                log_desc_l.append(content)
                log_sugg_l.append(log_sugg)

        pbar.close()
        # Store the results to dataframe and file
        self._summary_df['Time/LineNum'] = log_time_l
        self._summary_df['Severity'] = log_seve_l
        self._summary_df['Description'] = log_desc_l
        self._summary_df['Suggestion'] = log_sugg_l

        # Aggregate summaries and remove duplicates
        summary_top = list(dict.fromkeys(log_sugg_l))

        # Save the top summary to a file
        with open(self.fzip['top'], 'w', encoding='utf-8') as outfile:
            if len(summary_top) > 0:
                for idx, item in enumerate(summary_top):
                    outfile.write(''.join([str(idx+1), ') ', item]))
                    outfile.write('\n')
            else:
                outfile.write("Oops, the wrong logs are not in the knowledge-base. "
                              "Feed Back Please by clicking the link above.")

        # Save the summary data frame to file
        self._summary_df.to_csv(self.fzip['sum'], index=False,
            columns=["Time/LineNum", "Severity", "Description", "Suggestion"])
