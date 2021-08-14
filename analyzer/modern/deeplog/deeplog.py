# Licensed under the MIT License - see License.txt
""" DeepLog module
"""
import logging
from typing import List
from analyzer.modern import ModernBase

__all__ = ["DeepLog"]


log = logging.getLogger(__name__)

class DeepLog(ModernBase):
    """ The class of DeepLog technique """
    def __init__(self):
        ModernBase.__init__(self)


    def train(self):
        """ Train model.
        """


    def predict(self):
        """ Predict using mdoel.
        """
