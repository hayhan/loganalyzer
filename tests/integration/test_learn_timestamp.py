# Licensed under the MIT License - see LICENSE.txt
""" Integration tests
"""
import os
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser


def test_learn_timestamp():
    """ Detect timestamp width """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overwrite config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'OLDSCHOOL'

    ppobj = pp.Preprocess()

    # Copy the following raw file to data/cooked/cm/test.txt
    filelst: str = ['abnormal_1_diplexer_211.txt']
    ppobj.cat_files_lst(os.path.join(dh.RAW_DATA, 'abnormal'), filelst)

    ppobj.preprocess_ts()
    ps_ts_obj = Parser(ppobj.normlogs)
    ps_ts_obj.parse()
    ps_ts_obj.det_timestamp()

    assert GC.conf['general']['head_offset'] == 24
