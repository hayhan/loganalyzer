# Licensed under the MIT License - see License.txt
""" Utils to handle data folder """
import os
import sys
from analyzer.config import GlobalConfig

__all__ = [
    "ANALYZER_DATA",
    "RAW_DATA",
    "COOKED_DATA",
    "PERSIST_DATA",
    "TRAIN_DATA",
    "TEST_DATA",
    "TMP_DATA",
    "LOG_TYPE",
    "TRAINING",
]


try:
    ANALYZER_DATA = os.environ['ANALYZER_DATA']
except KeyError:
    print("Enviroment var ANALYZER_DATA is not set!!! Abort!!!")
    sys.exit(1)

try:
    LOG_TYPE = GlobalConfig.conf['general']['log_type']
except KeyError:
    # Populate the config dict in memory with config file contents. Suppose this only
    # happens once as we always update the GlobalConfig dict in memory in the running.
    GlobalConfig.read()
    LOG_TYPE = GlobalConfig.conf['general']['log_type']

RAW_DATA = os.path.join(ANALYZER_DATA, 'raw', LOG_TYPE)
COOKED_DATA = os.path.join(ANALYZER_DATA, 'cooked', LOG_TYPE)
PERSIST_DATA = os.path.join(ANALYZER_DATA, 'persist', LOG_TYPE)
TRAIN_DATA = os.path.join(ANALYZER_DATA, 'train', LOG_TYPE)
TEST_DATA = os.path.join(ANALYZER_DATA, 'test', LOG_TYPE)
TMP_DATA = os.path.join(ANALYZER_DATA, 'tmp')

TRAINING = GlobalConfig.conf['general']['training']
