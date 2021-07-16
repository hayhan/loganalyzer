# Licensed under the MIT License - see License.txt
""" Command line tool to check various things about a Loganalyzer installation.
"""
import logging
import warnings
import click


log = logging.getLogger(__name__)


@click.group("check")
def cli_check():
    """ Run checks for Loganalyzer """


@cli_check.command("logging")
def cli_check_logging():
    """ Check logging """
    log.debug("this is log.debug() output")
    log.info("this is log.info() output")
    log.warning("this is log.warning() output")
    warnings.warn("this is warnings.warn() output")
    print("this is stdout output")
