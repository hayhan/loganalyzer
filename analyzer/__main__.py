# Licensed under the MIT License - see LICENSE.txt
""" Top-level script environment for Loganalyzer.

This is what's executed when you run:

    'python -m analyzer' or simply 'analyzer'

See https://docs.python.org/3/library/__main__.html
"""
import sys
from .scripts.main import cli


if __name__ == "__main__":
    sys.exit(cli())  # pylint:disable=no-value-for-parameter
