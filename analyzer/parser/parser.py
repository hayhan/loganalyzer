# Licensed under the MIT License - see License.txt
""" Class of parser that wraps Drain """
import sys
import logging
from typing import List
from importlib import import_module
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC
from analyzer.parser import Para, Drain

# Load LOG_TYPE specific patterns
ptn = import_module("analyzer.parser." + dh.LOG_TYPE + '.patterns')

__all__ = ["Parser"]


log = logging.getLogger(__name__)

class Parser():
    """ The parser class """
    def __init__(self, rawlogs: List[str]):
        self.fzip: dict = dh.get_files_parser()
        self.training: bool = GC.conf['general']['training']
        self.metrics: bool = GC.conf['general']['metrics']
        self.context: str = GC.conf['general']['context']
        self.intmdt: bool = GC.conf['general']['intmdt']
        self.aim: bool = GC.conf['general']['aim']
        self._log_head_offset: int = GC.conf['general']['head_offset']
        self.rawlogs: List[str] = rawlogs
        self.df_raws = None
        self.df_tmplt = None

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

        my_parser = Drain(my_para, self.rawlogs)
        my_parser.main_process()
        self.df_raws = my_parser.df_raws
        self.df_tmplt = my_parser.df_tmplt
