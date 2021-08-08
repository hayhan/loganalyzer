# Licensed under the MIT License - see License.txt
""" CLI interface to the parser module.
"""
import logging
from importlib import import_module
import click
from analyzer.utils.data_helper import LOG_TYPE
from analyzer.config import GlobalConfig as GC
from analyzer.parser import Parser

# Load derived preprocess class module of LOG_TYPE
pp = import_module("analyzer.preprocess." + LOG_TYPE + '.preprocess')

log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# analyzer template updt
# ----------------------------------------------------------------------
@click.command(name="updt")
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
def cli_updt_tmplt(training, overwrite):
    """ Generate, update the template lib from raw data. """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = training
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'TEMPUPDT'
    GC.conf['general']['intmdt'] = True

    ppobj = pp.Preprocess()
    if overwrite:
        # _ToDo: give a confirmation prompt in console
        log.info("Delete the template library.")

    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    # Process the raw data and generate new data
    ppobj.preprocess_new()

    # Normalize the new data to generate norm data
    ppobj.preprocess_norm()

    # Remove the abnormal labels from norm data if any exist.
    ppobj.extract_labels()

    # Parsing using the norm data
    psobj = Parser()
    psobj.parse()

    log.info("The templates are generated / updated.")
