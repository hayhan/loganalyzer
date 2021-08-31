# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to utils.
"""
import os
import re
import logging
from typing import List
from datetime import datetime
from shutil import copyfile
import click
import analyzer.utils.data_helper as dh
import analyzer.utils.misc_tools as mt
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
    help="Source path and name, e.g. persist vocab_loglab.txt",
    show_default=True,
)
def cli_chkdup(src):
    """ Check duplicates in files """
    path, name = src
    mt.check_duplicates(path, name)

    log.info("Check duplicates done.")


# ----------------------------------------------------------------------
# analyzer utils normts
# ----------------------------------------------------------------------
@click.command(name="normts")
def cli_normts():  # pylint: disable=too-many-locals
    """ Normalize timestamps of raw logs. """
    tmp_dir = dh.TMP_DATA
    work_dir = dh.COOKED_DATA

    # Support sub-folders
    for dirpath, _, files in sorted(os.walk(tmp_dir, topdown=True)):
        # print(f'Found directory: {dirpath}')

        # Get the current system time
        dt_timestamp = datetime.now().timestamp()

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

            # Populate the in-memory config singleton with config file
            GC.read()
            # Set the items here
            GC.conf['general']['training'] = False
            GC.conf['general']['metrics'] = False
            GC.conf['general']['context'] = 'OLDSCHOOL'
            GC.conf['general']['intmdt'] = True

            # Sync the config update in memory to file?
            # GC.write()

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
                print("Warning: It looks file {} is not {} log.".format(filename, dh.LOG_TYPE))
                continue

            # Pattern for detected timestamp, aka. the log head offset
            pattern_timestamp = re.compile(r'.{%d}' % log_offset)

            # Replace the old timestamp (including no timestamp) with
            # the standard format.
            out_logs: List[str] = []
            with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                for line in rawin:
                    if pattern_timestamp.match(line):
                        #
                        dt_obj = datetime.fromtimestamp(dt_timestamp)
                        dt_format = '[' + dt_obj.strftime("%Y%m%d-%H:%M:%S.%f")[0:21] + '] '
                        # This works even log_offset is zero, aka. no
                        # old timestamp.
                        newline = pattern_timestamp.sub(dt_format, line, count=1)
                        # Increase 100ms per line
                        dt_timestamp += 0.100000
                    else:
                        # Messed lines, skip
                        continue
                    out_logs.append(newline)

            with open(newf, 'w', encoding='utf-8') as fout:
                fout.writelines(out_logs)

    log.info("Normalization done.")
