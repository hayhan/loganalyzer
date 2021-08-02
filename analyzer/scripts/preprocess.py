# Licensed under the MIT License - see License.txt
""" CLI interface to the preprocess module.
"""
import logging
from importlib import import_module
import click
from analyzer.config import GlobalConfig as GC
from analyzer.utils.data_helper import LOG_TYPE

# Load derived preprocess class module of LOG_TYPE
pp = import_module("analyzer.preprocess." + LOG_TYPE + '.preprocess')


log = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# analyzer preprocess new
# ----------------------------------------------------------------------
@click.command(name="new")
@click.option(
    "--training/--no-training",
    default=True,
    help="Change to training phase.",
    show_default=True,
)
def cli_gen_new(training):
    """ Preprocess the raw log file to generate new log file. """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = training
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'TEMPUPDT'
    GC.conf['general']['intmdt'] = True
    # Sync the config update in memory to file. Really necessary?
    # GC.write()

    ppobj = pp.Preprocess()
    ppobj.preprocess_new()

    log.info("The new log dataset is generated.")


# ----------------------------------------------------------------------
# analyzer preprocess norm
# ----------------------------------------------------------------------
@click.command(name="norm")
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
def cli_gen_norm(training, overwrite):
    """ Preprocess the raw log file to generate norm log file. """
    # Populate the in-memory config singleton with config file
    GC.read()
    # Set the items here
    GC.conf['general']['training'] = training
    GC.conf['general']['metrics'] = False
    GC.conf['general']['context'] = 'TEMPUPDT'
    GC.conf['general']['intmdt'] = True

    ppobj = pp.Preprocess()
    if overwrite:
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
