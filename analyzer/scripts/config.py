# Licensed under the MIT License - see License.txt
""" Interface to the global config file.
"""
import sys
import logging
import subprocess
import click
from analyzer.config import GlobalConfig, CONFIG_FILE

log = logging.getLogger(__name__)

@click.command(name="show")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help="Show the configuration values.",
    show_default=True,
)
def cli_show_config(filename):
    """ Show configuration file. """
    print(GlobalConfig.read_pretty(filename))
    log.info("Configuration file showed: %s", filename)


@click.command(name="edit")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help="Edit the configuration values.",
    show_default=True,
)
def cli_edit_config(filename):
    """ Edit configuration file. """
    subprocess.run(["vim", filename], check=False)
    log.info("Configuration file opened in editor: %s", filename)


@click.command(name="default")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help=" Default the configuration values.",
    show_default=True,
)
def cli_default_config(filename):
    """ Default configuration file. """
    GlobalConfig.default(filename)
    log.info("Configuration file defaulted: %s", filename)


@click.command(name="updt")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help="Update the configuration file.",
    show_default=True,
)
@click.option(
    "--intv",
    is_flag=True,
    default=False,
    help="Update integer value.",
    show_default=True,
)
@click.option(
    "--item",
    type=(str, str, str),
    help="Update the key-value pair in the configuration file.",
    show_default=True,
)
def cli_update_config(filename, intv, item):
    """ Update the key-value pair. """
    if item is None:
        print("Please define at least the key-value pair.")
        sys.exit()
    sect, key, val = item
    if intv:
        val = int(val)
    GlobalConfig.read(filename)
    GlobalConfig.conf[sect][key] = val
    GlobalConfig.write(filename)
    log.info("Configuration file updated: %s", filename)
