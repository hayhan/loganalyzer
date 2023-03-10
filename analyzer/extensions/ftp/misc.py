# Licensed under the MIT License - see LICENSE.txt
""" Miscellaneous stuff. LOG_TYPE specific.
"""
__all__ = [
]


# ======================================================================
# Preprocess module
# ======================================================================

# ======================================================================
# Parser module
# ======================================================================

# Special templates, for case 2 in the algorithm of recovering messed
# logs. Search the id in the template lib to match the real templates.
# It can be empty list.
SPECIAL_ID = []

# The first char to care about in recovering of messed logs
HEADER_CARE = []

# The max num of logs in which we search for m2 in the algorithm of
# recovering messed logs.
SCAN_RANGE = 20

# Log format. The LOG_FORMAT_COMPLETE and LOG_FORMAT_NOTS are parsed
# word by word, aka. each tag domain is separated by space. The last
# tag (usually <Content>) has the remaining words.
LOG_FORMAT_COMPLETE = '<Date> <Time> <Content>'
LOG_FORMAT_NOTS = '<Content>'

def log_format_custom(timestamp_width: int):
    """ Customized log format """
    return f'(?P<Time>.{{{timestamp_width}}})(?P<Content>.*?)'

# ======================================================================
# Other modules
# ======================================================================

# The head_offset in config file is the content offset. If log format is
# '<Time> <Content>', this offset value is also the timestamp width that
# includes the space in between. If log format is something like below
# '<Date> <Time> <Level> <Content>', we cannot use head_offset as width.
# Also for unknown log format (usually unknown timestamp), the offset in
# config file will be overwritten in memory when learning timestamp. So
# we record the standard timestamp width here for reference.
STD_TIMESTAMP_WIDTH = 20
STD_TIMESTAMP_FORMAT = "%Y%m%d %H:%M:%S"
STD_TIMESTAMP_FORMAT2 = STD_TIMESTAMP_FORMAT

def std_timestamp(datetime: str):
    """ Format standard timestamp """
    dt_format: str = datetime[0:STD_TIMESTAMP_WIDTH] + ' '
    return dt_format
