# Licensed under the MIT License - see License.txt
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


@cli.group("config", short_help="Show or edit the config file")
def cli_config():
    """ Show or edit the config file.

    \b
    - The sub-command `show` will print the config content
    \b
    - The sub-command `edit` will open the config content in vim editor
    \b
    - The sub-command `default` will default the config content
    \b
    - The sub-command `updt` will update the item in the config directly
      The option `type` sets the value type, e.g. int/bool/str(default)

    \b
    Examples
    --------

    \b
    $ analyzer config show
    $ analyzer config edit
    $ analyzer config default
    $ analyzer config updt --item key1 key2 val [--type int/bool/str]
    """


@cli.group("preprocess", short_help="Preprocess raw logs")
def cli_preprocess():
    """ Clean, restruct and normalize raw logs.

    \b
    - The option `src` will denote the raw data source folder. We use
      all log files under data/raw by default
    \b
    - The option `current` will use existing data/cooked/train.txt or
      test.txt directly.
    \b
    - The option `training` will denote the training or test phase.
    \b
    - The option `overwrite` will generate new log data again. Otherwise
      it will use existing new log file.

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
    - The option `src` will denote the raw data source folder. We use
      all log files under data/raw by default
    \b
    - The option `current` will use existing data/cooked/train.txt or
      test.txt directly.
    \b
    - The option `overwrite` will delete the template lib firstly.
    \b
    - The option `training` will denote the training or test phase.

    \b
    Examples
    --------

    \b
    $ analyzer template updt [--src folder]
    $ analyzer template updt [--current] [--overwrite]
    $ analyzer template updt [--training/no-training]
    $ analyzer template del
    """


@cli.group("oldschool", short_help="Analyze logs using oldschool")
def cli_oldschool():
    """ Oldschool for analyzing logs, and maintaining of knowledge-base.

    \b
    - The option `learn-ts` will learn the width of timestamp

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
    - The option `mykfold` will use kfold cross-verification manually
    \b
    - The option `model` will train / predict using the model assigned
      here instead of the one in the config file.
    \b
    - The option `adm` will train/predict using all defined models
    \b
    - The option `learn-ts` will learn the width of timestamp
    \b
    - The option `feat` will display the features of test logs

    \b
    Examples
    --------

    \b
    $ analyzer loglab train [--mykfold] [--model name] [--debug] [--adm]
    $ analyzer loglab predict [--model name] [--debug] [--adm]
    $ analyzer loglab predict [--learn-ts/--no-learn-ts] [--feat]
    """


@cli.group("deeplog", short_help="DeepLog method of log anomaly detection")
def cli_deeplog():
    """ DeepLog method of log anomaly detection.

    \b
    - The option `adm` will train/predict using all defined models param
    \b
    - The option `learn-ts` will learn the width of timestamp
    \b
    - The option `src` will validate the given folder, otherwise it will
      validate the existing test.txt in data/cooked.
    \b
    - The option `recover` will try to recover the messed logs because
      of multi threads.

    \b
    Examples
    --------

    \b
    $ analyzer deeplog train [--debug] [--adm]
    $ analyzer deeplog validate [--debug] [--adm] [--src folder]
    $ analyzer deeplog predict [--debug] [--adm] [--recover]
    $ analyzer deeplog predict [--learn-ts/--no-learn-ts]
    """


# pylint:disable=too-many-locals
def add_subcommands():
    """ add subcommands dynamically """
    # pylint:disable=import-outside-toplevel

    from .info import cli_info
    cli.add_command(cli_info)

    from .check import cli_check
    cli.add_command(cli_check)

    from .config import cli_show_config
    cli_config.add_command(cli_show_config)

    from .config import cli_edit_config
    cli_config.add_command(cli_edit_config)

    from .config import cli_default_config
    cli_config.add_command(cli_default_config)

    from .config import cli_update_config
    cli_config.add_command(cli_update_config)

    from .preprocess import cli_gen_new
    cli_preprocess.add_command(cli_gen_new)

    from .preprocess import cli_gen_norm
    cli_preprocess.add_command(cli_gen_norm)

    from .parser import cli_updt_tmplt
    cli_template.add_command(cli_updt_tmplt)

    from .parser import cli_del_tmplt
    cli_template.add_command(cli_del_tmplt)

    from .oldschool import cli_run_oss
    cli_oldschool.add_command(cli_run_oss)

    from .loglab import cli_loglab_train
    cli_loglab.add_command(cli_loglab_train)

    from .loglab import cli_loglab_predict
    cli_loglab.add_command(cli_loglab_predict)

    from .deeplog import cli_deeplog_train
    cli_deeplog.add_command(cli_deeplog_train)

    from .deeplog import cli_deeplog_validate
    cli_deeplog.add_command(cli_deeplog_validate)

    from .deeplog import cli_deeplog_predict
    cli_deeplog.add_command(cli_deeplog_predict)


add_subcommands()
