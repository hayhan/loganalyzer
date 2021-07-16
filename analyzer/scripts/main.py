# Licensed under the MIT License - see License.txt
""" Loganalyzer command line interface (scripts).
"""
import logging
import sys
import warnings
from pathlib import Path
import click
from analyzer import __version__


# We implement the --version following the example from here:
# https://click.palletsprojects.com/en/latest/options/#callbacks-and-eager-options
def print_version(ctx, param, value):  # pylint:disable=unused-argument
    """ Version info."""
    if not value or ctx.resilient_parsing:
        return
    print(f"Loganalyzer version {__version__}")
    ctx.exit()

# https://click.palletsprojects.com/en/latest/documentation/#help-parameter-customization
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group("analyzer", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--log-level",
    default="info",
    help="Logging verbosity level.",
    type=click.Choice(["debug", "info", "warning", "error"]),
)
@click.option("--ignore-warnings", is_flag=True, help="Ignore warnings?")
@click.option(
    "--version",
    is_flag=True,
    callback=print_version,
    expose_value=False,
    is_eager=True,
    help="Print version and exit.",
)
def cli(log_level, ignore_warnings):
    """ Loganalyzer command line interface (CLI).

    Loganalyzer is a Python package for log analyzing.

    Use ``--help`` to see available sub-commands, as well as the available
    arguments and options for each sub-command.

    \b
    Examples
    --------

    \b
    $ analyzer --help
    $ analyzer --version
    $ analyzer info --help
    $ analyzer info
    """
    logging.basicConfig(level=log_level.upper())

    if ignore_warnings:
        warnings.simplefilter("ignore")


@cli.group("config", short_help="Show or edit the config file")
def cli_config():
    """ Show or edit the config file.

    \b
    Examples
    --------

    \b
    $ analyzer config show
    $ analyzer config edit --logtype my/type
    """


@cli.group("preprocess", short_help="Preprocess raw logs")
def cli_preprocess():
    """ Clean, restruct and normalize raw logs.

    \b
    Examples
    --------

    \b
    $ analyzer preprocess new
    $ analyzer preprocess norm --overwrite
    """


@cli.group("template", short_help="Generate and update templates")
def cli_template():
    """ Parse logs, generate and update templates.

    \b
    Examples
    --------

    \b
    $ analyzer template updt
    $ analyzer template updt --overwrite
    $ analyzer template updt --src my/folder
    $ analyzer template del
    """


@cli.group("loglab", short_help="Multi-classification of log anomalies")
@click.pass_context
def cli_loglab(ctx):
    """ Multi-classification of log anomalies.

    \b
    - The option `kfold-manu` will use kfold cross-verification implemented manually.
    \b
    - The option `model` will train / predict using the model assigned here instead
    of the one in the config file.

    \b
    Examples
    --------

    \b
    $ analyzer loglab train
    $ analyzer loglab train --kfold-manu
    $ analyzer loglab train --model model-name
    $ analyzer loglab predict
    $ analyzer loglab predict --model model-name
    $ analyzer loglab feat
    """


def add_subcommands():
    """ add subcommands dynamically """
    from .info import cli_info                  # pylint:disable=import-outside-toplevel

    cli.add_command(cli_info)

    from .check import cli_check                # pylint:disable=import-outside-toplevel

    cli.add_command(cli_check)

    from .config import cli_show_config         # pylint:disable=import-outside-toplevel

    cli_config.add_command(cli_show_config)

    from .config import cli_update_config       # pylint:disable=import-outside-toplevel

    cli_config.add_command(cli_update_config)

add_subcommands()
