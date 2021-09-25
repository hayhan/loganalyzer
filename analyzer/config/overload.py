# Licensed under the MIT License - see LICENSE.txt
""" Handle the overloaded config file.
"""
import os
import sys
import logging
import analyzer.utils.data_helper as dh
import analyzer.utils.yaml_helper as yh
from analyzer.config import GlobalConfig as GC


__all__ = ["overload"]

log = logging.getLogger(__name__)


def overload():
    """ Update im-momory base conf with the overloaded config file. """
    if os.path.exists(dh.CONFIG_OVERLOAD):
        conf_overload: dict = yh.read_yaml(dh.CONFIG_OVERLOAD)
        for sec, attr in conf_overload.items():
            for key, val in attr.items():
                try:
                    GC.conf[sec][key] = val
                except KeyError:
                    print("The oerloaded config file has section/key \
                           that don't exist in base config!!! Abort!!!")
                    sys.exit(1)
