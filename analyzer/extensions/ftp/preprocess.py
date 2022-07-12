# Licensed under the MIT License - see LICENSE.txt
""" Derived class of preprocess. LOG_TYPE specific.
"""
import logging
from typing import Any, Dict
from analyzer.preprocess import PreprocessBase
from . import patterns as ptn


__all__ = ["Preprocess"]

log = logging.getLogger(__name__)


class Preprocess(PreprocessBase):
    """ The class of preprocess. """
    def __init__(self):
        PreprocessBase.__init__(self)
        self.ptn_main_ts = ptn.PTN_STD_TS

    def process_for_domain(self, line: str, state: Dict[str, Any]):
        """ Special line process for LOG_TYPE """
        del state

        #
        # Remove unwanted chars
        #
        line = ptn.PTN_CLEAN_CHAR.sub('', line)

        #
        # Replace customized response status with normalized one
        #
        for cur_rex, cur_log in ptn.PTN_RSP_STAT.items():
            if cur_rex.match(line):
                line = cur_log
                break

        return line

    def split_tokens(self, line: str, lite: bool):
        """ Split some token apart per the regx patterns """
        del lite
        line = self.split_token_apart(line, ptn.PTN_SPLIT_LEFT,
                                      ptn.PTN_SPLIT_RIGHT)
        return line

    def clean_misc_char(self, line: str):
        """ Clean console prompt, unwanted chars, etc """
        return ptn.PTN_CLEAN_CHAR.sub('', line)

    def match_session_label(self, line: str):
        """ Match session label for DeepLog """
        return ptn.PTN_SESSION.match(line)
