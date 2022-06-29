# Licensed under the MIT License - see LICENSE.txt
""" The re patterns for preprocess module. Common for all LOG_TYPEs.
"""
import re


__all__ = [
    "PTN_SEG_LABEL",
    "PTN_CLASS_LABEL",
    "PTN_ABN_LABEL",
    "PTN_NESTED_LINE",
]


PTN_SEG_LABEL = re.compile(
    # Pattern for segment labels, 'segsign: ' or 'cxxx '
    r'(segsign: )|(c[0-9]{3} )'
)

PTN_SEG_LABEL_1 = re.compile(
    # Pattern for segment label, 'segsign: '
    r'segsign: '
)

PTN_SEG_LABEL_2 = re.compile(
    # Pattern for segment label, 'cxxx: '
    r'c[0-9]{3} '
)

PTN_CLASS_LABEL = re.compile(
    # Pattern for class label 'cxxx'
    r'c[0-9]{3}'
)

PTN_ABN_LABEL = re.compile(
    # Pattern for abnormal label, 'abn: '
    r'abn: '
)

PTN_NESTED_LINE = re.compile(
    # Pattern for nested line
    r' +|\t+'
)

PTN_EMPTY_LINE = re.compile(
    # Pattern for empty line
    r'^[ \t]*$'
)

PTN_FUZZY_TIME = re.compile(
    # Pattern for time format, e.g. 12:34:56, 12-34-56, 12/34/56, etc.
    r'[0-5][0-9][^a-zA-Z0-9 ][0-5][0-9][^a-zA-Z0-9 ][0-5][0-9]'
)
