# Licensed under the MIT License - see License.txt
""" Access, update the global configuration.
"""
import logging
from pathlib import Path
from analyzer.utils.config_helper import read_yaml, read_yaml_pretty, write_yaml

log = logging.getLogger(__name__)

__all__ = ["GlobalConfig", "CONFIG_FILE"]

CONFIG_FILE = Path(__file__).resolve().parent / "config.yaml"


class GlobalConfig:
    """ Loganalyzer global configuration. """
    @classmethod
    def read(cls, path):
        """ Reads from YAML file. """
        config = read_yaml(path)
        return config

    @classmethod
    def read_pretty(cls, path):
        """ Reads from YAML file for pretty display. """
        config_format = read_yaml_pretty(path)
        return config_format

    @classmethod
    def update(cls, dictionary, path):
        """ Update YAML file. """
        write_yaml(dictionary, path)
