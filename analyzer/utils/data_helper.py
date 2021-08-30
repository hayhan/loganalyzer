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
    "get_files_io",
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
VOCAB_LOGLAB = os.path.join(PERSIST_DATA, 'vocab_loglab.npy')
VOCAB_DEEPLOG = os.path.join(PERSIST_DATA, 'vocab_deeplog.npy')
VOCAB_LOGLIZER = os.path.join(PERSIST_DATA, 'vocab_loglizer.npy')
VOCAB_LOGLIZER_STATIC = os.path.join(PERSIST_DATA, 'vocab_loglizer_static.npy')

# Skip file list when concatenates raw log files under data/raw
SKIP_FILE_LIST = ['README.md', 'desc.txt', 'train.lst', 'validate.lst']

# Max length of customized timestamp in logs for prediction
MAX_TIMESTAMP_LENGTH = 50
# Standard timestamp length including the last space
STD_TIMESTAMP_LENGTH = 24
# Length of abnormal label 'abn: ', including the last space
ABN_LABEL_LENGTH = 5
# Length of segment label 'segsign: ', including the last space
SEG_LABEL_LENGTH = 9
# Length of abnormal label 'cxxx ', including the last space
CLASS_LABEL_LENGTH = 5


def get_files_io():
    """ Collect the files of input / output. Mainly for debugging except
        analyzing results.
    """
    if GC.conf['general']['training']:
        files_zip = {
            'raw': os.path.join(COOKED_DATA, 'train.txt'),
            'new': os.path.join(COOKED_DATA, 'train_new.txt'),
            'norm': os.path.join(COOKED_DATA, 'train_norm.txt'),
            'labels': os.path.join(TRAIN_DATA, 'train_norm.txt_labels.pkl'),
            'segll': os.path.join(TRAIN_DATA, 'train_norm.txt_seginf_loglab.pkl'),
            'segdl': os.path.join(TRAIN_DATA, 'train_norm.txt_seginf_deeplog.pkl'),
            'struct': os.path.join(TRAIN_DATA, 'train_norm.txt_structured.csv'),
            'output': TRAIN_DATA

        }
    else:
        files_zip = {
            'raw': os.path.join(COOKED_DATA, 'test.txt'),
            'new': os.path.join(COOKED_DATA, 'test_new.txt'),
            'norm': os.path.join(COOKED_DATA, 'test_norm.txt'),
            'labels': os.path.join(TEST_DATA, 'test_norm.txt_labels.pkl'),
            'segll': os.path.join(TEST_DATA, 'test_norm.txt_seginf_loglab.pkl'),
            'segdl': os.path.join(TEST_DATA, 'test_norm.txt_seginf_deeplog.pkl'),
            'map_norm_raw': os.path.join(TEST_DATA, 'map_norm_raw.pkl'),
            'map_norm_rcv': os.path.join(TEST_DATA, 'map_norm_rcv.pkl'),
            'norm_rcv': os.path.join(TEST_DATA, 'test_norm_rcv.txt'),
            'struct': os.path.join(TEST_DATA, 'test_norm.txt_structured.csv'),
            'struct_rcv': os.path.join(TEST_DATA, 'test_norm_rcv.txt_structured.csv'),
            'top': os.path.join(TEST_DATA, 'analysis_summary_top.txt'),
            'sum': os.path.join(TEST_DATA, 'analysis_summary.csv'),
            'rst_llab': os.path.join(TEST_DATA, 'results_loglab.txt'),
            'rst_dlog': os.path.join(TEST_DATA, 'results_deeplog.txt'),
            'rst_llzr': os.path.join(TEST_DATA, 'results_loglizer.csv'),
            'dbg': os.path.join(TEST_DATA, 'debug.csv'),
            'output': TEST_DATA
        }
    return files_zip


def get_data_type():
    """ Data type string """
    if GC.conf['general']['training']:
        datatype = 'train'
    else:
        datatype = 'test'

    return datatype
