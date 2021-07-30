# Licensed under the MIT License - see License.txt
""" Base class of preprocess.
"""
import re
import sys
from abc import ABC, abstractmethod
from typing import List, Pattern
import logging
from analyzer.config import GlobalConfig
import analyzer.utils.data_helper as datahelp

__all__ = [
    "PTN_STD_TS",
    "PTN_LABEL",
    "PreprocessBase",
]

log = logging.getLogger(__name__)

PTN_STD_TS = re.compile(
    # Standard timestamp from console tool, e.g. [20190719-08:58:23.738]
    # Also add Loglizer Label, Deeplog segment sign, Loglab class label.
    r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
    r'\.(\d{3})|24:00:00\.000)\] (abn: )?(segsign: )?(c[0-9]{3} )?'
)
PTN_LABEL = re.compile(
    # Pattern for segment labels, 'segsign: ' or 'cxxx '
    r'(segsign: )|(c[0-9]{3} )'
)

class PreprocessBase(ABC):
    """ The base class of preprocess. """
    # pylint:disable=too-many-instance-attributes
    def __init__(self):
        self.fzip: dict = datahelp.get_files_preprocess()
        self.datatype: str = datahelp.get_data_type()
        self.training: bool = GlobalConfig.conf['general']['training']
        self.metrics: bool = GlobalConfig.conf['general']['metrics']
        self.context: str = GlobalConfig.conf['general']['context']
        self.intmdt: bool = GlobalConfig.conf['general']['intmdt']
        self.aim: bool = GlobalConfig.conf['general']['aim']

        self.newlogs: List[str] = []
        self.normlogs: List[str] = []

        # The main timestamp flag. The default offset value is from
        # the standard format
        self._reserve_ts: bool = True
        self._log_head_offset: int = GlobalConfig.conf['general']['head_offset']
        self.ptn_main_ts : Pattern = PTN_STD_TS

        # For prediction only. Does not include Loglizer.
        if not self.training:
            self.raw_ln_idx_new: List[int] = []
            self.raw_ln_idx_norm: List[int] = []

    def _main_timestamp_regx(self):
        """ Get timestamp regx pattern object. """
        if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
            and not (self.training or self.metrics):
            self.ptn_main_ts = re.compile(r'.{%d}' % self._log_head_offset)
        else:
            self.ptn_main_ts = PTN_STD_TS

    def _get_timestamp_info(self):
        """ Get updated timestamp info. """
        if self._log_head_offset > 0:
            self._reserve_ts = True
        elif self._log_head_offset == 0:
            self._reserve_ts = False
        else:
            # Not a LOG_TYPE log file
            sys.exit("It looks not {} log!".format(datahelp.LOG_TYPE))
        # Update main timestamp pattern object
        self._main_timestamp_regx()

    @property
    def log_head_offset(self):
        """ Get log head offset info. """
        return self._log_head_offset

    @log_head_offset.setter
    def log_head_offset(self, head_offset):
        """ Set log head offset info.
            Timestamp learnning will set the log_head_offset member as
            well as the config field in memory and file.
            \b
            - offset == -1: Not valid log file for LOG_TYPE
            - offset ==  0: Valid log file without timestamp
            - offset >   0: Valid log file with timestamp
        """
        self._log_head_offset = head_offset

    @abstractmethod
    def preprocess_ts(self):
        """ Preprocess before learning timestamp width.
            Only for prediction of (OSS, DeepLog or Loglab).
            Not for Loglizer as it requires timestamps for windowing.
        """

    @abstractmethod
    def preprocess_new(self):
        """ Preprocess to generate the new log data.
            Clean the raw log data.
        """

    def preprocess_norm(self):
        """ Preprocess to generate the norm log data.
            Normalize the new log data, aka. converting multi-line log
            to one line.
        """
