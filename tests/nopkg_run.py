# Licensed under the MIT License - see LICENSE.txt
""" Entry for non-package running (debug/test only).
"""
import sys
from utils import PROJ

sys.path.append(PROJ)

# pylint:disable=wrong-import-position
from analyzer.scripts.main import cli


cli()  # pylint:disable=no-value-for-parameter
