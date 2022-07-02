# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to utils.
"""
import os
import sys
import logging
from typing import List
from datetime import datetime
from shutil import copyfile
import click
import numpy as np
import analyzer.utils.data_helper as dh
import analyzer.utils.misc_tools as mt
import analyzer.utils.visualization as vz
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser


log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# analyzer utils chkdup
# ----------------------------------------------------------------------
@click.command(name="chkdup")
@click.option(
    "--src",
    nargs=2,
    type=str,
    required=True,
    help="Folder and file in data, e.g. persist vocab_loglab.npy.txt",
    show_default=True,
)
@click.option(
    "--ecm",
    default=False,
    is_flag=True,
    help="Checking duplicates of featrue vector in event matrix.",
    show_default=True,
)
def cli_chk_duplicate(src, ecm):
    """ Check duplicate lines in a txt file """
    subd, name = src

    file_loc: str = os.path.join(dh.ANALYZER_DATA, subd, dh.LOG_TYPE, name)
    if not os.path.exists(file_loc):
        print("File does not exist!!!")
        sys.exit(1)
    with open(file_loc, 'r', encoding='utf-8') as fout:
        strings: List[str] = fout.readlines()

    dups: List[List[int]] = []

    # The saved ecm has label vector at last column. Split matrix apart
    # into body and label vector.
    if ecm:
        mtx: List[str] = []
        labels: List[str] = []
        dups_with_label: List[List[str]] = []

        for line in strings:
            cells = line.strip('\r\n').split()
            labels.append(''.join(['Class_', cells[-1][:-2]]))
            mtx.append(' '.join(cells[:-1]))

        dups = mt.check_duplicates(mtx)

        for dup in dups:
            dups_with_label.append([''.join([str(idx+1), '/', labels[idx]]) for idx in dup])
        print("Duplicate sets:\n", dups_with_label)

    else:
        dups = mt.check_duplicates(strings)
        print("Duplicate sets:\n", dups)

    log.info("Check duplicates done.")


# ----------------------------------------------------------------------
# analyzer utils normts
# ----------------------------------------------------------------------
@click.command(name="normts")
def cli_norm_timestamp():  # pylint: disable=too-many-locals
    """ Normalize timestamps of raw logs. """
    tmp_dir = dh.TMP_DATA
    work_dir = dh.COOKED_DATA

    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = False
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'OLDSCHOOL'

    # Sync the config update in memory to file?
    # GC.write()

    # Get current system time
    dt_timestamp = datetime.now().timestamp()

    # Support sub-folders
    for dirpath, _, files in sorted(os.walk(tmp_dir, topdown=True)):
        # print(f'Found directory: {dirpath}')

        for filename in files:
            # Skip hidden files if any exist
            if filename[0] == '.':
                continue

            newfile = 'new_' + filename
            rawf = os.path.join(dirpath, filename)
            dstf = os.path.join(work_dir, 'test.txt')
            newf = os.path.join(dirpath, newfile)
            # print(rawf)

            copyfile(rawf, dstf)

            ppobj = pp.Preprocess()

            # Load existing test.txt
            ppobj.load_raw_logs()

            # Learn the width of timestamp
            ppobj.preprocess_ts()
            ps_ts_obj = Parser(ppobj.normlogs)
            ps_ts_obj.parse()
            ps_ts_obj.det_timestamp()

            # Read the width of timestamp, we just learned
            log_offset = GC.conf['general']['head_offset']
            if log_offset < 0:
                print(f"Warning: It looks file {filename} is not {dh.LOG_TYPE} log.")
                continue

            # Normalize the timestamps and save to a new file
            dt_timestamp = mt.norm_timestamp(rawf, newf, log_offset, dt_timestamp)

    log.info("Normalization done.")


# ----------------------------------------------------------------------
# analyzer utils eidlog
# ----------------------------------------------------------------------
@click.command(name="eidlog")
@click.option(
    "--eid",
    required=True,
    help="The event id to be matched in raw log file.",
    show_default=True,
)
@click.option(
    "--training/--no-training",
    default=True,
    help="Select train or test data file in data/cooked.",
    show_default=True,
)
def cli_eid_log(eid, training):
    """ Find the logs that match the given event id in raw log file. """
    # Populate the in-memory config singleton with the base config file
    # and then update with the overwrite config file. Use GC.read() if
    # only want the base config file.
    dh.GCO.read()
    # Set the items here
    GC.conf['general']['training'] = training
    GC.conf['general']['metrics'] = False

    # Sync the config update in memory to file?
    # GC.write()

    mt.find_logs_by_eid(eid, training)


# ----------------------------------------------------------------------
# analyzer utils viz
# ----------------------------------------------------------------------
@click.command(name="viz")
@click.option(
    "--src",
    nargs=2,
    type=str,
    required=True,
    help="Indicate folder and file in data, e.g. train vocab_loglab.txt.",
    show_default=True,
)
@click.option(
    "--label",
    default=False,
    is_flag=True,
    help="Annotate each dot in the plot with target label.",
    show_default=True,
)
def cli_visualize_data(src, label):
    """ Visualize dataset """
    subd, name = src

    file_loc: str = os.path.join(dh.ANALYZER_DATA, subd, dh.LOG_TYPE, name)
    if not os.path.exists(file_loc):
        print("File does not exist!!!")
        sys.exit(1)
    with open(file_loc, 'r', encoding='utf-8') as fout:
        strings: List[str] = fout.readlines()

    # The saved ecm has label vector at last column. Split them.
    mtx: List[List[str]] = []
    targets: List[int] = []
    for line in strings:
        cells = line.strip('\r\n').split()
        mtx.append(cells[:-1])
        targets.append(int(cells[-1][:-2]))

    mtx_2d = np.array(mtx, dtype=float)
    print(mtx_2d.dtype, mtx_2d.shape, targets)
    vz.visualize_with_umap(mtx_2d, targets, label)

    log.info("Visualization done.")
