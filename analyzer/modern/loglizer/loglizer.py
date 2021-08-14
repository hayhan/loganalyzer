# Licensed under the MIT License - see License.txt
""" Loglizer module
"""
import logging
from typing import List
from analyzer.modern import ModernBase

__all__ = ["Loglizer"]


log = logging.getLogger(__name__)

class Loglizer(ModernBase):
    """ The class of Loglizer technique """
    def __init__(self):
        ModernBase.__init__(self)


    def train(self):
        """ Train model.
        """


    def predict(self):
        """ Predict using mdoel.
        """
