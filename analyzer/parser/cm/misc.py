# Licensed under the MIT License - see LICENSE.txt
""" The misc stuff. LOG_TYPE specific.
"""
__all__ = [
    "SPECIAL_ID",
    "HEADER_CARE",
    "SCAN_RANGE",
]

# Special templates, for case 2 of recovering of messed logs
SPECIAL_ID = ['b9c1fdb1']

# The first char to care about in the recovering of messed logs
HEADER_CARE = ['L', 'C']

# The logs that we find m2 in the the recovering of messed logs
SCAN_RANGE = 20
