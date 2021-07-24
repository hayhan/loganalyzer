# Licensed under the MIT License - see License.txt
""" Base class of preprocess.
"""
import re
import sys
from abc import ABC, abstractmethod
from typing import List
import logging
from analyzer.config import GlobalConfig
import analyzer.utils.data_helper as datahelp

__all__ = [
    "STD_TS_PTTN",
    "PreprocessBase",
]


log = logging.getLogger(__name__)

STD_TS_PTTN = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
                         r'\.(\d{3})|24:00:00\.000)\] (abn: )?(segsign: )?(c[0-9]{3} )?')


class PreprocessBase(ABC):
    """ The base class of preprocess. """
    # pylint:disable=too-many-instance-attributes
    def __init__(self):
        self.fzip: dict = datahelp.get_files_preprocess()
        self.datatype: str = datahelp.get_data_type()
        self.training: bool = GlobalConfig.conf['general']['training']
        self.metrics: bool = GlobalConfig.conf['general']['metrics']
        self.context: str = GlobalConfig.conf['general']['context']

        # The main timestamp flag. The default offset value is from
        # the standard format
        self.reserve_ts: bool = True
        self.log_head_offset: int = GlobalConfig.conf['general']['head_offset']

        # For prediction only. Not include Loglizer.
        if not self.training:
            self.raw_ln_idx_new: List[int] = []
            self.raw_ln_idx_norm: List[int] = []

    def get_timestamp_info(self):
        """ Get updated timestamp info """
        if self.log_head_offset > 0:
            self.reserve_ts = True
        elif self.log_head_offset == 0:
            self.reserve_ts = False
        else:
            # Not a LOG_TYPE log file
            sys.exit("It looks not {} log!".format(datahelp.LOG_TYPE))

    @abstractmethod
    def preprocess_ts(self):
        """ Preprocess before learning timestamp width.
            Only for prediction of (OSS, DeepLog or Loglab).
            Not for Loglizer as it requires timestamps for windowing.
        """

    @abstractmethod
    def preprocess_new(self):
        """ Preprocess to generate new log data.
            Clean the raw log data.
        """

    def preprocess_norm(self):
        """ Preprocess to generate norm log data.
            Normalize the new log data, aka. converting multi-line log
            to one line.
        """
