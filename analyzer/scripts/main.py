# Licensed under the MIT License - see LICENSE.txt
""" Loganalyzer command line interface (scripts).
"""
import logging
import warnings
import click
from analyzer import __version__


# We implement the --version following the example from here:
# https://click.palletsprojects.com/en/latest/options/#callbacks-and-eager-options
def print_version(ctx, param, value):  # pylint:disable=unused-argument
    """ Version info. """
    if not value or ctx.resilient_parsing:
        return
    print(f"Loganalyzer version {__version__}")
    ctx.exit()


# https://click.palletsprojects.com/en/latest/documentation/#help-parameter-customization
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group("analyzer", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--log-level",
    default="warning",
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
@click.pass_context
def cli(ctx, log_level, ignore_warnings):
    """ Loganalyzer command line interface (CLI).

    Loganalyzer is a Python package for log analyzing.

    Use ``--help`` to see available sub-commands, as well as the
    available arguments and options for each sub-command.

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

    # Lazy loading of the second level sub-commands

    # Set invoke_without_command=True in group property otherwise cli()
    # cannot be invoked without sub-command. Do not enable it currently.
    # https://click.palletsprojects.com/en/latest/commands/

    # pylint:disable=import-outside-toplevel
    if ctx.invoked_subcommand is None:
        click.echo('I was invoked without sub command.')

    elif ctx.invoked_subcommand == 'config':
        from . import config as mod
        cli_config.add_command(mod.cli_show_config)
        cli_config.add_command(mod.cli_edit_config)
        cli_config.add_command(mod.cli_default_config)
        cli_config.add_command(mod.cli_update_config)

    elif ctx.invoked_subcommand == 'preprocess':
        from . import preprocess as mod
        cli_preprocess.add_command(mod.cli_gen_new)
        cli_preprocess.add_command(mod.cli_gen_norm)

    elif ctx.invoked_subcommand == 'template':
        from . import parser as mod
        cli_template.add_command(mod.cli_updt_tmplt)
        cli_template.add_command(mod.cli_del_tmplt)
        cli_template.add_command(mod.cli_sort_tmplt)

    elif ctx.invoked_subcommand == 'oldschool':
        from .oldschool import cli_run_oss
        cli_oldschool.add_command(cli_run_oss)

    elif ctx.invoked_subcommand == 'loglab':
        from . import loglab as mod
        cli_loglab.add_command(mod.cli_loglab_train)
        cli_loglab.add_command(mod.cli_loglab_predict)

    elif ctx.invoked_subcommand == 'deeplog':
        from . import deeplog as mod
        cli_deeplog.add_command(mod.cli_deeplog_train)
        cli_deeplog.add_command(mod.cli_deeplog_validate)
        cli_deeplog.add_command(mod.cli_deeplog_predict)

    elif ctx.invoked_subcommand == 'loglizer':
        from . import loglizer as mod
        cli_loglizer.add_command(mod.cli_loglizer_train)
        cli_loglizer.add_command(mod.cli_loglizer_validate)
        cli_loglizer.add_command(mod.cli_loglizer_predict)

    elif ctx.invoked_subcommand == 'utils':
        from . import utils as mod
        cli_utils.add_command(mod.cli_chk_duplicate)
        cli_utils.add_command(mod.cli_norm_timestamp)
        cli_utils.add_command(mod.cli_eid_log)
    else:
        click.echo('Cannot happen.')


@cli.group("config", short_help="Show or edit the config file")
def cli_config():
    """ Show or edit the config file.

    \b
    - The sub-command `show` prints the config content
    \b
    - The sub-command `edit` opens the config content in vim editor
    \b
    - The sub-command `default` defaults the config content
    \b
    - The sub-command `updt` updates the item in the config directly
      The option `type` sets the value type, e.g. int/bool/str(default)
    \b
    - The option `overload` indicates the overloaded config file

    \b
    Examples
    --------

    \b
    $ analyzer config show [--overload]
    $ analyzer config edit [--overload]
    $ analyzer config default
    $ analyzer config updt --item key1 key2 val [--type int/bool/str]
    $ analyzer config updt --overload
    """


@cli.group("preprocess", short_help="Preprocess raw logs")
def cli_preprocess():
    """ Clean, restruct and normalize raw logs.

    \b
    - The option `src` denotes the raw data source folder. We use all
      log files under data/raw by default.
    \b
    - The option `current` uses existing data/cooked/train.txt or the
      test.txt directly.
    \b
    - The option `training` denotes the training or test phase.
    \b
    - The option `overwrite` generates new log data again. Otherwise it
      uses existing new log file.

    \b
    Examples
    --------

    \b
    $ analyzer preprocess new [--training] [--src folder] [--current]
    $ analyzer preprocess norm [--training] [--src folder] [--current]
    $ analyzer preprocess norm [--overwrite]
    """


@cli.group("template", short_help="Generate and update templates")
def cli_template():
    """ Parse logs, generate and update templates.

    \b
    - The option `src` denotes the raw data source folder. We use all
      log files under data/raw by default.
    \b
    - The option `current` uses existing data/cooked/train.txt or the
      test.txt directly.
    \b
    - The option `overwrite` deletes the template lib firstly.
    \b
    - The option `training` denotes the training or test phase.

    \b
    Examples
    --------

    \b
    $ analyzer template updt [--src folder] [--debug]
    $ analyzer template updt [--current] [--overwrite]
    $ analyzer template updt [--training/no-training]
    $ analyzer template del
    $ analyzer template sort
    """


@cli.group("oldschool", short_help="Analyze logs using oldschool")
def cli_oldschool():
    """ Oldschool for analyzing logs, and maintaining of knowledge-base.

    \b
    - The option `learn-ts` learns the width of timestamp.

    \b
    Examples
    --------

    \b
    $ analyzer oldschool run [--learn-ts/--no-learn-ts]
    """


@cli.group("loglab", short_help="Multi-classification of log anomalies")
def cli_loglab():
    """ Multi-classification of log anomalies.

    \b
    - The option `model` trains/predicts using the model assigned here
      instead of the one in the config file.
    \b
    - The option `mykfold` uses kfold cross-verification manually
    \b
    - The option `adm` trains/predicts using all defined models
    \b
    - The option `learn-ts` learns the width of timestamp
    \b
    - The option `feat` displays the features of test logs

    \b
    Examples
    --------

    \b
    $ analyzer loglab train [--model name] [--mykfold] [--adm] [--debug]
    $ analyzer loglab predict [--model name] [--adm] [--debug]
    $ analyzer loglab predict [--learn-ts/--no-learn-ts] [--feat]
    """


@cli.group("deeplog", short_help="DeepLog method of log anomaly detection")
def cli_deeplog():
    """ DeepLog method of log anomaly detection.

    \b
    - The option `adm` trains/predicts using all defined models param
    \b
    - The option `learn-ts` learns the width of timestamp
    \b
    - The option `src` validates the given folder, otherwise it will
      validate the existing test.txt in data/cooked directory.

    \b
    Examples
    --------

    \b
    $ analyzer deeplog train [--adm] [--debug]
    $ analyzer deeplog validate [--adm] [--src folder] [--debug]
    $ analyzer deeplog predict [--adm] [--debug]
    $ analyzer deeplog predict [--learn-ts/--no-learn-ts]
    """


@cli.group("loglizer", short_help="Loglizer method of log anomaly detection")
def cli_loglizer():
    """ Loglizer method of log anomaly detection.

    \b
    - The option `model` trains/predicts using the model assigned here
      instead of the one in the config file.
    \b
    - The option `inc` trains models incrementally in one shot per the
      file list.
    \b
    - The option `adm` trains/predicts using all defined models param
    \b
    - The option `src` validates the given folder, otherwise it will
      validate the existing test.txt in data/cooked.

    \b
    Examples
    --------

    \b
    $ analyzer loglizer train [--model name] [--inc] [--adm] [--debug]
    $ analyzer loglizer validate [--model name] [--adm] [--debug]
    $ analyzer loglizer validate [--src folder]
    $ analyzer loglizer predict [--model name] [--adm] [--debug]
    """


@cli.group("utils", short_help="Some utils for helping debug/clean logs")
def cli_utils():
    """ Some utils for helping debug/clean logs.

    \b
    - The sub-command `chkdup` checks duplicate lines in a txt file in a
      folder in data directory. e.g. --src train ecm_loglab.txt.
      The option `ecm` is for checking event matrix of loglab/loglizer.
    \b
    - The sub-command `normts` normalizes timestamps of logs in data/tmp
      directory.
    \b
    - The sub-command `eidlog` finds all the logs that match the given
      event id in the raw log file.

    \b
    Examples
    --------

    \b
    $ analyzer utils chkdup --src folder fname [--ecm loglab/loglizer]
    $ analyzer utils normts
    $ analyzer utils eidlog --eid value [--training/--no-training]
    """


def add_subcommands():
    """ Add the first level sub-commands only. Lazy load others. """
    # pylint:disable=import-outside-toplevel

    from .info import cli_info
    cli.add_command(cli_info)

    from .check import cli_check
    cli.add_command(cli_check)


add_subcommands()
