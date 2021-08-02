# Licensed under the MIT License - see License.txt
""" The re patterns for preprocess module. Common for all LOG_TYPEs.
"""
import re

__all__ = [
    "PTN_STD_TS",
    "PTN_SEG_LABEL",
    "PTN_ABN_LABEL",
    "PTN_NESTED_LINE",
]

PTN_STD_TS = re.compile(
    # Standard timestamp from console tool, e.g. [20190719-08:58:23.738]
    # Also add Loglizer Label, Deeplog segment sign, Loglab class label.
    r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
    r'\.(\d{3})|24:00:00\.000)\] (abn: )?(segsign: )?(c[0-9]{3} )?'
)

PTN_SEG_LABEL = re.compile(
    # Pattern for segment labels, 'segsign: ' or 'cxxx '
    r'(segsign: )|(c[0-9]{3} )'
)

PTN_ABN_LABEL = re.compile(
    # Pattern for abnormal label, 'abn: '
    r'abn: '
)

PTN_NESTED_LINE = re.compile(
    # Pattern for nested line
    r' +|\t+'
)
