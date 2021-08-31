# Licensed under the MIT License - see LICENSE.txt
""" API for preprocess module.
"""
from importlib import import_module
import analyzer.utils.data_helper as dh

__all__ = ["pp"]

# Load derived preprocess class module of LOG_TYPE
pp = import_module("analyzer.preprocess." + dh.LOG_TYPE + ".preprocess")
