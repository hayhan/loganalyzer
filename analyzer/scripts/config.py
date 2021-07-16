# Licensed under the MIT License - see License.txt
""" Interface to the global config file.
"""
import logging
import click
from analyzer.config import GlobalConfig

log = logging.getLogger(__name__)


@click.command(name="show")
@click.option(
    "--filename",
    default="config.yaml",
    help="Show the configuration values.",
    show_default=True,
)
def cli_show_config(filename):
    """ Show configuration file. """
    print(GlobalConfig.read_pretty(filename))
    log.info("Configuration file showed: %s", filename)


@click.command(name="updt")
@click.option(
    "--filename",
    default="config.yaml",
    help="Update the configuration file.",
    show_default=True,
)
@click.option(
    "--item",
    type=(str, str, str),
    help="Update the key-value pair in the configuration file.",
    show_default=True,
)
def cli_update_config(filename, item):
    """ Update the key-value pair. """
    sect, key, val = item
    config = GlobalConfig.read(filename)
    config[sect][key] = val
    GlobalConfig.update(config, filename)
    log.info("Configuration file updated: %s", filename)
