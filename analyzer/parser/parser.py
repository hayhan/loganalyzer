# Licensed under the MIT License - see LICENSE.txt
""" Class of parser that wraps Drain """
import sys
import re
import logging
import hashlib
import pickle
from typing import List
from importlib import import_module
#import pandas as pd
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC
from analyzer.parser import Para, Drain

# Load LOG_TYPE specific patterns
ptn = import_module("analyzer.parser." + dh.LOG_TYPE + ".patterns")
msc = import_module("analyzer.parser." + dh.LOG_TYPE + ".misc")

__all__ = ["Parser"]


log = logging.getLogger(__name__)

# pylint: disable=too-many-instance-attributes
class Parser():
    """ The parser class """
    def __init__(self, rawlogs: List[str], rcv: bool = False):
        self.fzip: dict = dh.get_files_io()
        self.training: bool = GC.conf['general']['training']
        self.metrics: bool = GC.conf['general']['metrics']
        self.context: str = GC.conf['general']['context']
        self.intmdt: bool = GC.conf['general']['intmdt']
        self.aim: bool = GC.conf['general']['aim']
        self.rcv: bool = rcv
        self._rawlogs: List[str] = rawlogs  # Norm data from preprocess
        self._log_head_offset: int = GC.conf['general']['head_offset']
        self._map_norm_raw: List[int] = []
        self._map_norm_rcv: List[int] = []
        self._norm_rcv: List[str] = []
        self._df_raws = None
        self._df_tmplts = None


    @property
    def df_raws(self):
        """ Get raws (structured) in pandas dataframe
            Column: LineId/Time/Content/EventIdOld/EventId/EventTemplate
        """
        return self._df_raws


    @property
    def df_tmplts(self):
        """ Get templates in pandas dataframe
            Column: EventIdOld/EventId/EventTemplate/Occurrences
        """
        return self._df_tmplts


    @property
    def map_norm_raw(self):
        """ Get the raw line index in norm data """
        return self._map_norm_raw


    @map_norm_raw.setter
    def map_norm_raw(self, map_norm_raw: List[int]):
        """ Set the raw line index in norm data """
        self._map_norm_raw = map_norm_raw


    @property
    def map_norm_rcv(self):
        """ Get the norm line index in mess recovered norm data """
        return self._map_norm_rcv


    @property
    def norm_rcv(self):
        """ Get the mess recovered norm data """
        return self._norm_rcv


    def parse(self):
        """ Parse, generate and update templates """
        # For Loglab/DeepLog predict and OSS, check the runtime log head
        # off value to decide the timestamp width.
        if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
            and not (self.training or self.metrics):
            if self._log_head_offset == 0:
                log_format = '<Content>'
            elif self._log_head_offset > 0:
                # The customized pattern does not remove trailing spaces
                # behind timestamp comparing to the standard / default
                # format. This does not matter for DeepLog, Loglab and
                # OSS as we only display the timestamps. For Loglizer,
                # we should calculate the time window and should take
                # care when this change affacts it in the future.
                log_format = '(?P<Time>.{%d})(?P<Content>.*?)' % self._log_head_offset
            else:
                log.info("Not %s log, Return right now.", dh.LOG_TYPE)
                sys.exit(0)
        else:
            log_format = '<Time> <Content>'

        # Do the 2nd round parsing for the recovered norm data
        if self.rcv:
            ptn_hard_para = {}
            raw_file = self.fzip['norm_rcv']
        else:
            ptn_hard_para = ptn.PTN_HARD_PARA
            raw_file = self.fzip['norm']

        my_para = Para(
            log_format, ptn_hard_para, ptn.PTN_SPEC_TOKEN, raw_file, dh.TEMPLATE_LIB,
            outdir=self.fzip['output'], over_wr_lib=self.training, intmdt=self.intmdt,
            aim=self.aim, inc_updt=1, prt_tree=0, nopgbar=0
        )

        my_parser = Drain(my_para, self._rawlogs)
        my_parser.main_process()

        # Reload the magazine of our parser gun
        #
        # Column: LineId/Time/Content/EventIdOld/EventId/EventTemplate
        self._df_raws = my_parser.df_raws

        # For in-memory template lib, it is always the same as the data
        # in lib file except 'Occurrences' for training. It is probably
        # different for prediction as we dont overwrite lib file with
        # the parsing result. So reload the non-updated version.
        if self.training:
            # Column: EventIdOld/EventId/EventTemplate/Occurrences
            self._df_tmplts = my_parser.df_tmplts
        else:
            # Column: EventIdOld/EventId/EventTemplate
            self._df_tmplts = my_parser.df_tmplts_o


    def learn_timestamp(self):
        """ Learn the width of timestamp. Run parse beforehand. """
        # Load event id from template library
        eid_lib: List[str] = self._df_tmplts['EventId'].values.tolist()

        # Take the structured logs
        content_logs: List[str] = self._df_raws['Content'].values.tolist()
        temp_logs: List[str] = self._df_raws['EventTemplate'].values.tolist()

        # Init offset as -1 which means a non LOG_TYPE log file
        log_start_offset: int = -1
        idx: int = 0

        for idx, (content, temp) in enumerate(zip(content_logs, temp_logs)):
            # Slice one char at the head of current template, and then
            # hash the remaining.
            for i in range(len(temp)):
                if i > dh.MAX_TIMESTAMP_LENGTH:
                    break
                temp_tail = temp[i:]
                eid_tail = hashlib.md5(temp_tail.encode('utf-8')).hexdigest()[0:8]
                if eid_tail in eid_lib:
                    if i == 0:
                        # No timestamp at all, we can return directly
                        log_start_offset = 0
                        return log_start_offset, idx

                    # Take out the first word (append a space) of the
                    # template and locate where it is in the raw log
                    # (content).
                    header = temp[i:].split()[0]+' '
                    match = re.search(header, content)
                    if match:
                        log_start_offset = match.start()
                        return log_start_offset, idx
                    # For some reason we cannot locate the header in the
                    # raw log, go to check the next log
                    break

        return log_start_offset, idx


    def det_timestamp(self):
        """ Get the width of timestamp and update config setting """
        self._log_head_offset, lineoffset = self.learn_timestamp()
        # Updat the global config setting on the fly
        GC.conf['general']['head_offset'] = self._log_head_offset

        log.debug("Learned log head offset: %d, at line %d.",
                  self._log_head_offset, lineoffset)


    # pylint: disable=too-many-locals:too-many-branches
    # pylint: disable=too-many-statements
    def rcv_mess(self):
        """ Recover messed logs (test.txt) caused by multi threads
            See design doc to understand the algorithm. Run parse
            beforehand.

            Currently this file is ONLY used for DeepLog predict.
            Not for DeepLog train and validation.
            Not for OSS, Loglab and Loglizer.
        """
        # Load event id from template library
        eid_lib: List[str] = self._df_tmplts['EventId'].values.tolist()

        # Load old event id & template of each log from structured norm
        if self._log_head_offset > 0:
            # Real timestamp plus a space
            time_logs = (self._df_raws['Time']+' ').values.tolist()
        elif self._log_head_offset == 0:
            # Empty string for each timestamp
            time_logs = [''] * self._df_raws.shape[0]
        else:
            log.info("Not LOG_TYPE log. Return right now.")
            sys.exit(1)

        eid_old_logs: List[str] = self._df_raws['EventIdOld'].values.tolist()
        temp_logs: List[str] = self._df_raws['EventTemplate'].values.tolist()

        # new_temp_logs = [0] * self._df_raws.shape[0]
        m1_found: bool = False
        o1_head: str = ''
        skipped_ln: int = []

        for idx, (eido, temp) in enumerate(zip(eid_old_logs, temp_logs)):
            # Check the first char
            header_care = temp[0] in msc.HEADER_CARE
            # Check th next log if current log id exists already in lib
            # or m1 has not been found and the log does not start with
            # the char defined in HEADER_CARE.
            if (eido != '0') or (not m1_found and not header_care):
                # new_temp_logs[idx] = temp
                self._map_norm_rcv.append(idx)
                self._norm_rcv.append(time_logs[idx]+temp+'\n')
                continue

            # We get here only when condition below:
            # (old event id is zero) AND (m1_found OR header_care)
            if m1_found:
                # Abort if we cannot find m2 within SCAN_RANGE logs
                if idx - m1_idx > msc.SCAN_RANGE:
                    # new_temp_logs[idx] = temp
                    self._map_norm_rcv.append(idx)
                    self._norm_rcv.append(time_logs[idx]+temp+'\n')
                    m1_found = False
                    continue
                # Note the eido == 0 here
                temp_o1 = o1_head + temp
                # new_temp_logs[idx] = temp_o1
                self._map_norm_rcv.append(idx)
                self._norm_rcv.append(time_logs[idx]+temp_o1+'\n')
                m1_found = False
                continue

            # We get here only when conditon below:
            # (old event id is zero) AND (m1_found==0 AND header_care)
            # The case 1, the most common case
            for i in range(len(temp)):
                o1_head = temp[0:i+1]
                temp_o2 = temp[i+1:]
                eid_o2 = hashlib.md5(temp_o2.encode('utf-8')).hexdigest()[0:8]
                if eid_o2 in eid_lib:
                    m1_found = True
                    m1_idx = idx
                    # new_temp_logs[idx] = temp_o2
                    self._map_norm_rcv.append(idx)
                    self._norm_rcv.append(time_logs[idx]+temp_o2+'\n')
                    if eid_o2 in msc.SPECIAL_ID:
                        # The case 2:
                        # Remove one trailing spaces in o1_head
                        o1_head = o1_head[0:-1]
                    break

            # If cannot find m1 in current log, we suppose o1 is broken
            # by o2 wherein a leading new line char exists. In other
            # words, we get here w/ m1_found == False because we are
            # encountering case 3.
            if not m1_found:
                # Skip writing the empty line to norm pred file
                # self._norm_rcv.append(time_logs[idx]+'\n')
                # new_temp_logs[idx] = ''

                # We write down the skipped line/log number, which will
                # be used to update the raw/norm file line mapping table
                skipped_ln.append(idx)

                # The o1_head now contains the whole m1, so we claim m1
                # is found.
                m1_found = True
                m1_idx = idx

        # Save the new temp/eid vector to a new norm test file
        # data_df = pd.DataFrame()
        # data_df['EventTemplate'] = new_temp_logs
        # data_df.to_csv(self.fzip['dbg'], index=False)

        # Update the raw / norm file line mapping table
        if len(skipped_ln) > 0:
            if not GC.conf['general']['aim']:
                with open(self.fzip['map_norm_raw'], 'rb') as fio:
                    self._map_norm_raw = pickle.load(fio)
            # reverse the list in skipped_ln before poping the empty lines
            for i in skipped_ln[::-1]:
                self._map_norm_raw.pop(i)
            if not GC.conf['general']['aim']:
                with open(self.fzip['map_norm_raw'], 'wb') as fio:
                    pickle.dump(self._map_norm_raw, fio)

        if not GC.conf['general']['aim']:
            with open(self.fzip['map_norm_rcv'], 'wb') as fio:
                pickle.dump(self._map_norm_rcv, fio)
            with open(self.fzip['norm_rcv'], 'w', encoding='utf-8') as fout:
                fout.writelines(self._norm_rcv)
