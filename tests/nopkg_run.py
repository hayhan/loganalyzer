# Licensed under the MIT License - see LICENSE.txt
""" Entry for non-package running (debug/test only).

This is what's executed when you run:

    'python nopkg_run.py'
"""
import sys
from utils import PROJ

sys.path.append(PROJ)

# pylint:disable=wrong-import-position
from analyzer.scripts.main import cli


if __name__ == "__main__":
    cli()  # pylint:disable=no-value-for-parameter
