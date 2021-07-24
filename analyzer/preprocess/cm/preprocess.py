# Licensed under the MIT License - see License.txt
""" Derived class of preprocess.
"""
import logging
import analyzer.utils.config_helper as confhelper
from analyzer.preprocess.preprocess_base import PreprocessBase

__all__ = [
    "Preprocess",
]


log = logging.getLogger(__name__)

class Preprocess(PreprocessBase):
    """ The class of preprocess. """
    def __init__(self):
        PreprocessBase.__init__(self)

    def preprocess_ts(self):
        """ Preprocess before learning timestamp width.
            Only for prediction of (OSS, DeepLog or Loglab)
            Not for Loglizer as it requires timestamps for windowing
        """
        log.info("Preprocess before timestamp detection.")

    def preprocess_new(self):
        """ Preprocess to generate new log data.
            Clean the raw log data.
        """
        log.info("Preprocess to generate new log data.")
