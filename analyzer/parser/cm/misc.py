# Licensed under the MIT License - see LICENSE.txt
""" Miscellaneous stuff. LOG_TYPE specific.
"""
__all__ = [
    "SPECIAL_ID",
    "HEADER_CARE",
    "SCAN_RANGE",
]


# Special templates, for case 2 in the algorithm of recovering messed
# logs. Search the id in the template lib to see the real templates. It
# can be empty list.
SPECIAL_ID = ['b9c1fdb1']

# The first char to care about in recovering of messed logs
HEADER_CARE = ['L', 'C']

# The max num of logs in which we search for m2 in the algorithm of
# recovering messed logs.
SCAN_RANGE = 20
