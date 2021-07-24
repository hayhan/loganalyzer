# Licensed under the MIT License - see License.txt
""" CLI interface to the preprocess module.
"""
import logging
from importlib import import_module
import click
from analyzer.config import GlobalConfig
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
    GlobalConfig.read()
    # Set the items here
    GlobalConfig.conf['general']['training'] = training
    GlobalConfig.conf['general']['metrics'] = False
    GlobalConfig.conf['general']['context'] = 'TEMPUPDT'
    GlobalConfig.conf['general']['intmdt'] = True
    # Sync the config update in memory to file. Really necessary?
    GlobalConfig.write()

    ppobj = pp.Preprocess()
    ppobj.preprocess_new()

    log.info("The new log file is generated.")


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
    GlobalConfig.read()
    # Set the items here
    GlobalConfig.conf['general']['training'] = training
    GlobalConfig.conf['general']['metrics'] = False
    GlobalConfig.conf['general']['context'] = 'TEMPUPDT'
    GlobalConfig.conf['general']['intmdt'] = True

    ppobj = pp.Preprocess()
    if overwrite:
        ppobj.preprocess_new()
    elif GlobalConfig.conf['general']['aim']:
        # Use existing new file to generate norm log, we then must set
        # general:aim field to false. The aim:true means always using
        # in-memory data.
        GlobalConfig.conf['general']['aim'] = False

    # Sync the config update in memory to file. Really necessary?
    GlobalConfig.write()
    ppobj.preprocess_norm()

    log.info("The norm log file is generated.")
