# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to the preprocess module.
"""
import os
import logging
import click
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC
from analyzer.config import overload as overload_conf
from analyzer.preprocess import pp


log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# analyzer preprocess new
# ----------------------------------------------------------------------
@click.command(name="new")
@click.option(
    "--src",
    default=dh.RAW_DATA,
    help="Choose source raw log files.",
    show_default=True,
)
@click.option(
    "--training/--no-training",
    default=True,
    help="Change to training phase.",
    show_default=True,
)
@click.option(
    "--current",
    default=False,
    is_flag=True,
    help="Use existing train.txt or test.txt.",
    show_default=True,
)
def cli_gen_new(src, training, current):
    """ Preprocess the raw log file to generate new log file. """
    # Populate the in-memory config singleton with the base config file
    GC.read()
    # Update with the overloaded config file
    overload_conf()
    # Set the items here
    GC.conf['general']['training'] = training
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'TEMPUPDT'
    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    # Get the raw data files from data/raw folder and cat/save them to
    # train.txt or test.txt in data/cooked.
    if not current:
        if src != dh.RAW_DATA:
            src = os.path.join(dh.RAW_DATA, src)
        ppobj.cat_files_dir(src)
    else:
        # Load existing tran.txt or test.txt
        ppobj.load_raw_logs()

    ppobj.preprocess_new()

    log.info("The new log dataset is generated.")


# ----------------------------------------------------------------------
# analyzer preprocess norm
# ----------------------------------------------------------------------
@click.command(name="norm")
@click.option(
    "--src",
    default=dh.RAW_DATA,
    help="Choose source raw log files.",
    show_default=True,
)
@click.option(
    "--training/--no-training",
    default=True,
    help="Change to training phase.",
    show_default=True,
)
@click.option(
    "--overwrite/--no-overwrite",
    default=True,
    help="Overwrite new log file, aka. generate new log from scratch.",
    show_default=True,
)
@click.option(
    "--current",
    default=False,
    is_flag=True,
    help="Use existing train.txt or test.txt.",
    show_default=True,
)
def cli_gen_norm(src, training, overwrite, current):
    """ Preprocess the raw log file to generate norm log file. """
    # Populate the in-memory config singleton with the base config file
    GC.read()
    # Update with the overloaded config file
    overload_conf()
    # Set the items here
    GC.conf['general']['training'] = training
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'TEMPUPDT'

    ppobj = pp.Preprocess()
    if overwrite:
        # Get the raw data files from data/raw folder and cat/save them
        # as train.txt or test.txt in data/cooked.
        if not current:
            if src != dh.RAW_DATA:
                src = os.path.join(dh.RAW_DATA, src)
            ppobj.cat_files_dir(src)
        else:
            # Load existing tran.txt or test.txt
            ppobj.load_raw_logs()

        ppobj.preprocess_new()
    elif GC.conf['general']['aim']:
        # Use existing new file to generate norm log, we then must set
        # general:aim field to false. The aim:true means always using
        # in-memory data.
        GC.conf['general']['aim'] = False

    # Sync the config update in memory to file. Really necessary?
    # GC.write()
    ppobj.preprocess_norm()
    # Remove the abnormal labels from norm dataset if any exist.
    ppobj.extract_labels()

    log.info("The norm log dataset is generated.")
