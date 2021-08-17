# Licensed under the MIT License - see License.txt
""" Utils to handle anything that are data/log related """
import os
import sys
from analyzer.config import GlobalConfig as GC

__all__ = [
    "ANALYZER_DATA",
    "RAW_DATA",
    "COOKED_DATA",
    "PERSIST_DATA",
    "TRAIN_DATA",
    "TEST_DATA",
    "TMP_DATA",
    "LOG_TYPE",
    "TEMPLATE_LIB",
    "SKIP_FILE_LIST",
    "get_files_preprocess",
    "get_files_parser",
    "get_files_oss",
    "get_data_type",
]


try:
    ANALYZER_DATA = os.environ['ANALYZER_DATA']
except KeyError:
    print("Enviroment var ANALYZER_DATA is not set!!! Abort!!!")
    sys.exit(1)

try:
    LOG_TYPE = GC.conf['general']['log_type']
except KeyError:
    # Populate the config dict in memory with config file contents.
    # Suppose this only happens once as we always update GC
    # dict in memory in the running.
    GC.read()
    LOG_TYPE = GC.conf['general']['log_type']

# The sub folders under top data directory
RAW_DATA = os.path.join(ANALYZER_DATA, 'raw', LOG_TYPE)
COOKED_DATA = os.path.join(ANALYZER_DATA, 'cooked', LOG_TYPE)
PERSIST_DATA = os.path.join(ANALYZER_DATA, 'persist', LOG_TYPE)
TRAIN_DATA = os.path.join(ANALYZER_DATA, 'train', LOG_TYPE)
TEST_DATA = os.path.join(ANALYZER_DATA, 'test', LOG_TYPE)
TMP_DATA = os.path.join(ANALYZER_DATA, 'tmp')
TEMPLATE_LIB = os.path.join(PERSIST_DATA, 'template_lib.csv')

# Skip file list when concatenates raw log files under data/raw
SKIP_FILE_LIST = ['README.md', 'desc.txt']

MAX_TIMESTAMP_LENGTH = 50

# Standard timestamp length including the last space
STD_TIMESTAMP_LENGTH = 24
# Length of abnormal label 'abn: ', including the last space
ABN_LABEL_LENGTH = 5
# Length of segment label 'segsign: ', including the last space
SEG_LABEL_LENGTH = 9
# Length of abnormal label 'cxxx ', including the last space
CLASS_LABEL_LENGTH = 5


def get_files_preprocess():
    """ Collect the files of input / output of preprocess """
    if GC.conf['general']['training']:
        files_zip = {
            'raw': os.path.join(COOKED_DATA, 'train.txt'),
            'new': os.path.join(COOKED_DATA, 'train_new.txt'),
            'norm': os.path.join(COOKED_DATA, 'train_norm.txt'),
            'label': os.path.join(TRAIN_DATA, 'train_norm.txt_labels.csv'),
            'segll': os.path.join(TRAIN_DATA, 'train_norm.txt_seginf_loglab.pkl'),
            'segdl': os.path.join(TRAIN_DATA, 'train_norm.txt_seginf_deeplog.pkl')

        }
    else:
        files_zip = {
            'raw': os.path.join(COOKED_DATA, 'test.txt'),
            'new': os.path.join(COOKED_DATA, 'test_new.txt'),
            'norm': os.path.join(COOKED_DATA, 'test_norm.txt'),
            'label': os.path.join(TEST_DATA, 'test_norm.txt_labels.csv'),
            'segll': os.path.join(TEST_DATA, 'test_norm.txt_seginf_loglab.pkl'),
            'segdl': os.path.join(TEST_DATA, 'test_norm.txt_seginf_deeplog.pkl'),
            'rawln_idx': os.path.join(TEST_DATA, 'rawline_idx_norm.pkl')
        }
    return files_zip


def get_files_parser():
    """ Collect the files of input / output of parser """
    if GC.conf['general']['training']:
        files_zip = {
            'norm': os.path.join(COOKED_DATA, 'train_norm.txt'),
            'output': TRAIN_DATA,
            'structured': os.path.join(TRAIN_DATA, 'train_norm.txt_structured.csv')
        }
    else:
        files_zip = {
            'norm': os.path.join(COOKED_DATA, 'test_norm.txt'),
            'output': TEST_DATA,
            'structured': os.path.join(TEST_DATA, 'test_norm.txt_structured.csv')
        }
    return files_zip


def get_files_oss():
    """ Collect the files of input / output of oss """
    assert GC.conf['general']['training'] is False

    files_zip = {
        'structured': os.path.join(TEST_DATA, 'test_norm.txt_structured.csv'),
        'rawln_idx': os.path.join(TEST_DATA, 'rawline_idx_norm.pkl'),
        'top': os.path.join(TEST_DATA, 'analysis_summary_top.txt'),
        'sum': os.path.join(TEST_DATA, 'analysis_summary.csv')
    }
    return files_zip


def get_data_type():
    """ Data type string """
    if GC.conf['general']['training']:
        datatype = 'train'
    else:
        datatype = 'test'

    return datatype
