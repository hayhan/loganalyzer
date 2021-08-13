# Licensed under the MIT License - see License.txt
""" Class of parser that wraps Drain """
import sys
import re
import logging
import hashlib
from typing import List
from importlib import import_module
import pandas as pd
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC
from analyzer.parser import Para, Drain

# Load LOG_TYPE specific patterns
ptn = import_module("analyzer.parser." + dh.LOG_TYPE + '.patterns')

__all__ = ["Parser"]


log = logging.getLogger(__name__)

# pylint: disable=too-many-instance-attributes
class Parser():
    """ The parser class """
    def __init__(self, rawlogs: List[str]):
        self.fzip: dict = dh.get_files_parser()
        self.training: bool = GC.conf['general']['training']
        self.metrics: bool = GC.conf['general']['metrics']
        self.context: str = GC.conf['general']['context']
        self.intmdt: bool = GC.conf['general']['intmdt']
        self.aim: bool = GC.conf['general']['aim']
        self._rawlogs: List[str] = rawlogs
        self._log_head_offset: int = GC.conf['general']['head_offset']
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

        my_para = Para(
            log_format, ptn.PTN_HARD_PARA, ptn.PTN_SPEC_TOKEN, self.fzip['norm'],
            dh.TEMPLATE_LIB, outdir=self.fzip['output'], over_wr_lib=self.training,
            intmdt=self.intmdt, aim=self.aim, inc_updt=1, prt_tree=0, nopgbar=0
        )

        my_parser = Drain(my_para, self._rawlogs)
        my_parser.main_process()

        # Reload the magazine of our parser gun
        #
        # Column: LineId/Time/Content/EventIdOld/EventId/EventTemplate
        self._df_raws = my_parser.df_raws
        # Column: EventIdOld/EventId/EventTemplate/Occurrences
        self._df_tmplts = my_parser.df_tmplts


    def learn_timestamp(self):
        """ Learn the width of timestamp """
        # Load event id from template library
        data_df = pd.read_csv(dh.TEMPLATE_LIB, usecols=['EventId'],
                              engine='c', na_filter=False, memory_map=True)
        eid_lib: List[str] = data_df['EventId'].values.tolist()

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
