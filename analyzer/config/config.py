# Licensed under the MIT License - see LICENSE.txt
""" Access, update the global configuration.
"""
import logging
from pathlib import Path
import analyzer.utils.config_helper as confhelp

__all__ = ["GlobalConfig", "CONFIG_FILE"]


log = logging.getLogger(__name__)

CONFIG_FILE = Path(__file__).resolve().parent / "config.yaml"
CONFIG_FILE_DEFAULT = Path(__file__).resolve().parent / "config.default.yaml"


class GlobalConfig:
    """ Loganalyzer global configuration. """
    # Expose this class dict intentionally for read and update.
    conf = {}

    @classmethod
    def read(cls, path=CONFIG_FILE):
        """ Reads from YAML file. Populate the conf member. """
        cls.conf = confhelp.read_yaml(path)

    @classmethod
    def read_pretty(cls, path=CONFIG_FILE):
        """ Reads from YAML file for pretty display. """
        config_format = confhelp.read_yaml_pretty(path)
        return config_format

    @classmethod
    def write(cls, path=CONFIG_FILE):
        """ Update YAML file. """
        confhelp.write_yaml(cls.conf, path)

    @classmethod
    def default(cls, path=CONFIG_FILE):
        """ Default YAML file. """
        confhelp.copy_file(path, CONFIG_FILE_DEFAULT)
