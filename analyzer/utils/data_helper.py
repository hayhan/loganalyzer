# Licensed under the MIT License - see License.txt
""" Utils to handle data folder """
import os

__all__ = [
    "ANALYZER_DATA",
]


try:
    ANALYZER_DATA = os.environ['ANALYZER_DATA']
except KeyError:
    ANALYZER_DATA = "NotSet"
