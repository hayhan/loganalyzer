# Licensed under the MIT License - see LICENSE.txt
""" Miscellaneous stuff. LOG_TYPE specific.
"""
__all__ = [
    "SPECIAL_ID",
    "HEADER_CARE",
    "SCAN_RANGE",
]


# Special templates, for case 2 in the algorithm of recovering messed
# logs. Search the id in the template lib to match the real templates.
# It can be empty list.
SPECIAL_ID = ['b9c1fdb1']

# The first char to care about in recovering of messed logs
HEADER_CARE = ['L', 'C']

# The max num of logs in which we search for m2 in the algorithm of
# recovering messed logs.
SCAN_RANGE = 20

# Log format. The LOG_FORMAT_COMPLETE and LOG_FORMAT_NOTS are parsed
# word by word, aka. each tag domain is separated by space. The last
# tag (usually <Content>) has the remaining words.
LOG_FORMAT_COMPLETE = '<Time> <Content>'
LOG_FORMAT_NOTS = '<Content>'

def log_format_custom(timestamp_width: int):
    """ Customized log format """
    return f'(?P<Time>.{{{timestamp_width}}})(?P<Content>.*?)'
