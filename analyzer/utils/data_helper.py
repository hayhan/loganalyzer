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
    "get_files_preprocess",
    "get_data_type",
]


try:
    ANALYZER_DATA = os.environ['ANALYZER_DATA']
except KeyError:
    print("Enviroment var ANALYZER_DATA is not set!!! Abort!!!")
    sys.exit(1)

try:
    LOG_TYPE = GlobalConfig.conf['general']['log_type']
except KeyError:
    # Populate the config dict in memory with config file contents.
    # Suppose this only happens once as we always update GlobalConfig
    # dict in memory in the running.
    GlobalConfig.read()
    LOG_TYPE = GlobalConfig.conf['general']['log_type']

# The sub folders under top data directory
RAW_DATA = os.path.join(ANALYZER_DATA, 'raw', LOG_TYPE)
COOKED_DATA = os.path.join(ANALYZER_DATA, 'cooked', LOG_TYPE)
PERSIST_DATA = os.path.join(ANALYZER_DATA, 'persist', LOG_TYPE)
TRAIN_DATA = os.path.join(ANALYZER_DATA, 'train', LOG_TYPE)
TEST_DATA = os.path.join(ANALYZER_DATA, 'test', LOG_TYPE)
TMP_DATA = os.path.join(ANALYZER_DATA, 'tmp')


def get_files_preprocess():
    """ List the files of input / output of preprocess """
    if GlobalConfig.conf['general']['training']:
        files_zip = {
            'raw': os.path.join(COOKED_DATA, 'train.txt'),
            'new': os.path.join(COOKED_DATA, 'train_new.txt'),
            'norm': os.path.join(COOKED_DATA, 'train_norm.txt')
        }
    else:
        files_zip = {
            'raw': os.path.join(COOKED_DATA, 'test.txt'),
            'new': os.path.join(COOKED_DATA, 'test_new.txt'),
            'norm': os.path.join(COOKED_DATA, 'test_norm.txt'),
            'runtime_para': os.path.join(TEST_DATA, 'test_runtime_para.txt'),
            'rawln_idx': os.path.join(TEST_DATA, 'rawline_idx_norm.pkl')
        }
    return files_zip


def get_data_type():
    """ Data type string """
    if GlobalConfig.conf['general']['training']:
        datatype = 'train'
    else:
        datatype = 'test'

    return datatype
