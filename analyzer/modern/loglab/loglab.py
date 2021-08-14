# Licensed under the MIT License - see License.txt
""" Loglab module
"""
import logging
from typing import List
from analyzer.modern import ModernBase

__all__ = ["Loglab"]


log = logging.getLogger(__name__)

class Loglab(ModernBase):
    """ The class of Loglab technique """
    def __init__(self):
        ModernBase.__init__(self)


    def train(self):
        """ Train model.
        """


    def predict(self):
        """ Predict using mdoel.
        """
