# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to the global config file.
"""
import os
import sys
import logging
import subprocess
import click
from analyzer.config import GlobalConfig as GC, CONFIG_FILE
from analyzer.utils.data_helper import CONFIG_OVERLOAD


log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# analyzer config show
# ----------------------------------------------------------------------
@click.command(name="show")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help="Show the configuration values.",
    show_default=True,
)
@click.option(
    "--overload",
    default=False,
    is_flag=True,
    help="Indicates the overloaded config file instead of the base one.",
    show_default=True,
)
def cli_show_config(filename, overload):
    """ Show configuration file. """
    if overload and os.path.exists(CONFIG_OVERLOAD):
        filename = CONFIG_OVERLOAD
    print(GC.read_pretty(filename))
    log.info("Configuration file showed: %s", filename)


# ----------------------------------------------------------------------
# analyzer config edit
# ----------------------------------------------------------------------
@click.command(name="edit")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help="Edit the configuration values.",
    show_default=True,
)
@click.option(
    "--overload",
    default=False,
    is_flag=True,
    help="Indicates the overloaded config file instead of the base one.",
    show_default=True,
)
def cli_edit_config(filename, overload):
    """ Edit the configuration file. """
    if overload and os.path.exists(CONFIG_OVERLOAD):
        filename = CONFIG_OVERLOAD
    subprocess.run(["vim", filename], check=False)
    log.info("Configuration file opened in editor: %s", filename)


# ----------------------------------------------------------------------
# analyzer config default
# ----------------------------------------------------------------------
@click.command(name="default")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help="Default the configuration values.",
    show_default=True,
)
def cli_default_config(filename):
    """ Default the configuration file. """
    GC.default(filename)
    log.info("Configuration file defaulted: %s", filename)


# ----------------------------------------------------------------------
# analyzer config updt
# ----------------------------------------------------------------------
@click.command(name="updt")
@click.option(
    "--filename",
    default=CONFIG_FILE,
    help="Update the configuration file.",
    show_default=True,
)
@click.option(
    "--type",
    default="str",
    help="Annotate the value type.",
    show_default=True,
)
@click.option(
    "--item",
    type=(str, str, str),
    help="Update the key-value pair in the configuration file.",
    show_default=True,
)
@click.option(
    "--overload",
    default=False,
    is_flag=True,
    help="Indicates the overloaded config file instead of the base one.",
    show_default=True,
)
# pylint:disable=redefined-builtin
def cli_update_config(filename, type, item, overload):
    """ Update the key-value pair. """
    if item is None:
        print("Please define at least the key-value pair.")
        sys.exit()
    sect, key, val = item
    if type == "int":
        val = int(val)
    elif type == "bool":
        val = val in ('True', 'true', '1')

    if overload and os.path.exists(CONFIG_OVERLOAD):
        filename = CONFIG_OVERLOAD

    GC.read(filename)
    GC.conf[sect][key] = val
    GC.write(filename)
    log.info("Configuration file updated: %s", filename)
