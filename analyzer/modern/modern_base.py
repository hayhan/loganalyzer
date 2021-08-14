# Licensed under the MIT License - see License.txt
""" Base class of modern analyzing techniques.
"""
import logging
from abc import ABC, abstractmethod
from typing import List
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh

__all__ = ["ModernBase"]


log = logging.getLogger(__name__)

class ModernBase(ABC):
    """ The base class of modern analyzing techniques. """
    def __init__(self):
        self.fzip: dict = dh.get_files_preprocess()
        self.training: bool = GC.conf['general']['training']
        self.metrics: bool = GC.conf['general']['metrics']
        self.context: str = GC.conf['general']['context']
        self.max_line: int = GC.conf['general']['max_line']

        # The structured normalized raw logs, aka. structured norm
        self._df_raws: List[str] = []


    @abstractmethod
    def train(self):
        """ Train model.
        """


    @abstractmethod
    def predict(self):
        """ Predict using mdoel.
        """
