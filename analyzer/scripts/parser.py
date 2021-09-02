# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to the parser module.
"""
import os
import logging
import click
import analyzer.utils.data_helper as dh
import analyzer.utils.misc_tools as mt
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import pp
from analyzer.parser import Parser


log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# analyzer template updt
# ----------------------------------------------------------------------
@click.command(name="updt")
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
    default=False,
    help="Overwrite the template library.",
    show_default=True,
)
@click.option(
    "--current",
    default=False,
    is_flag=True,
    help="Use existing train.txt or test.txt.",
    show_default=True,
)
def cli_updt_tmplt(src, training, overwrite, current):
    """ Generate, update the template lib from raw data. """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = training
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'TEMPUPDT'

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()

    if overwrite:
        log.info("Delete the template library.")
        try:
            os.remove(dh.TEMPLATE_LIB)
            os.remove(dh.TEMPLATE_LIB + '.old')
        except OSError:
            # Already removed
            pass

    # Get the raw data files from data/raw folder and cat/save them as
    # train.txt or test.txt in data/cooked.
    if not current:
        if src != dh.RAW_DATA:
            src = os.path.join(dh.RAW_DATA, src)
        ppobj.cat_files_dir(src)
        if training:
            # Exceptions for specific LOG_TYPE
            ppobj.exceptions_tmplt()
    else:
        # Load existing tran.txt or test.txt
        ppobj.load_raw_logs()

    # Process the raw data and generate new data
    ppobj.preprocess_new()

    # Normalize the new data to generate norm data
    ppobj.preprocess_norm()

    # Remove the abnormal labels from norm data if any exist.
    ppobj.extract_labels()

    # Parsing using the norm data
    psobj = Parser(ppobj.normlogs)
    psobj.parse()

    log.info("The templates are generated / updated.")

# ----------------------------------------------------------------------
# analyzer template del
# ----------------------------------------------------------------------
@click.command(name="del")
@click.confirmation_option(
    prompt='Are you sure you want to delete the template lib?'
)
def cli_del_tmplt():
    """ Delete the template lib. """
    try:
        os.remove(dh.TEMPLATE_LIB)
        os.remove(dh.TEMPLATE_LIB + '.old')
    except OSError as error:
        print(error)

    log.info("The template lib is removed.")

# ----------------------------------------------------------------------
# analyzer template sort
# ----------------------------------------------------------------------
@click.command(name="sort")
def cli_sort_tmplt():
    """ Sor the template lib for debugging. """
    mt.sort_tmplt_lib()
