# Licensed under the MIT License - see LICENSE.txt
""" Command line tool to check various things about a Loganalyzer
    package installation.
"""
import logging
import warnings
import click


log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# analyzer check
# ----------------------------------------------------------------------
@click.group("check")
def cli_check():
    """ Run checks for Loganalyzer """


# ----------------------------------------------------------------------
# analyzer check logging
# ----------------------------------------------------------------------
@cli_check.command("logging")
def cli_check_logging():
    """ Check logging """
    log.debug("this is log.debug() output")
    log.info("this is log.info() output")
    log.warning("this is log.warning() output")
    warnings.warn("this is warnings.warn() output")
    print("this is stdout output")
