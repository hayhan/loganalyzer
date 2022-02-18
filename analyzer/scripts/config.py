# Licensed under the MIT License - see LICENSE.txt
""" CLI interface to the global config file.
"""
import os
import sys
import shutil
import logging
import subprocess
import click
from analyzer.config import GlobalConfig as GC, CONFIG_FILE
from analyzer.utils.data_helper import CONFIG_OVERWRITE


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
    "--overwrite",
    default=False,
    is_flag=True,
    help="Indicates the overwrite config file instead of the base one.",
    show_default=True,
)
def cli_show_config(filename, overwrite):
    """ Show configuration file. """
    if overwrite and os.path.exists(CONFIG_OVERWRITE):
        filename = CONFIG_OVERWRITE
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
    "--overwrite",
    default=False,
    is_flag=True,
    help="Indicates the overwrite config file instead of the base one.",
    show_default=True,
)
def cli_edit_config(filename, overwrite):
    """ Edit the configuration file. """
    if overwrite and os.path.exists(CONFIG_OVERWRITE):
        filename = CONFIG_OVERWRITE

    cmd_exists = lambda x: shutil.which(x) is not None
    if cmd_exists("vim"):
        subprocess.run(["vim", filename], check=False)
    elif cmd_exists("vi"):
        subprocess.run(["vi", filename], check=False)
    else:
        print("Cannot find vim or vi editor. Try to use updt command.")
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
    "--mytype",
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
    "--overwrite",
    default=False,
    is_flag=True,
    help="Indicates the overwrite config file instead of the base one.",
    show_default=True,
)
def cli_update_config(filename, mytype, item, overwrite):
    """ Update the key-value pair. """
    if item is None:
        print("Please define at least the key-value pair.")
        sys.exit()
    sect, key, val = item
    if mytype == "int":
        val = int(val)
    elif mytype == "bool":
        val = val in ('True', 'true', '1')

    if overwrite and os.path.exists(CONFIG_OVERWRITE):
        filename = CONFIG_OVERWRITE

    GC.read(filename)
    GC.conf[sect][key] = val
    GC.write(filename)
    log.info("Configuration file updated: %s", filename)
