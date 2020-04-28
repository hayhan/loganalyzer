#!/usr/bin/env python3
"""
Description : This file adapts CM log from boardfarm system to the preprocessor
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

raw_file_loc  = parentdir + '/logs/test_boardfarm.txt'
new_file_loc  = parentdir + '/logs/test.txt'

"""
The original log usually comes from serial console tools like SecureCRT
in Windows and the text file encoding is probably utf-8 (with BOM).
https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8

To let python skip the BOM when decoding the file, use utf-8-sig codec.
https://docs.python.org/3/library/codecs.html
"""
rawfile    = open(raw_file_loc, 'r', encoding='utf-8-sig')
newfile    = open(new_file_loc, 'w')

"""
Definitions:
primary line - no space proceeded
nested line  - one or more spaces proceeded
empty line   - LF or CRLF only in one line
"""

"""
Patterns for removing normal timestamp and abnormal timestamp
"""
# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738]. Label is also considered.
strPattern0 = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)\.(\d{3})|24:00:00\.000)\] ')
strPattern1 = re.compile(r' \[ *\d+\]')

"""
Pattern for nested line
"""
nestedLinePattern = re.compile(r' +')


"""
Recover the timestamps of some lines
"""

# The lastLine is initialized as empty w/o LF or CRLF
lastline = ''
lastlineTS = '[19700101-00:00:00.000]'
currlineTS = '[19700101-00:00:00.000]'
recovContxt = False

for line in rawfile:
    matchTS = strPattern0.match(line)
    matchAbnTS = strPattern1.match(line)
    # Match the normal timestamp
    if matchTS:
        currlineTS = matchTS.group(0)
    # Match the abnormal timestamp
    elif matchAbnTS:
        # Replace current line abnormal timestamp with last line normal one
        line = strPattern1.sub(lastlineTS, line, count=1)
    # Other kind of line headings except both normal and abnormal timestamp
    else:
        # Not match the normal timestamp, and it is a primary line
        if not line in ['\n', '\r\n'] and not nestedLinePattern.match(line):
            if recovContxt:
                # Remove the LF or CRLF of last line
                lastline = lastline.rstrip() + ' '
        else:
            recovContxt = False

    # Start the recover context
    if matchTS or matchAbnTS:
        lineNoTS = strPattern0.sub('', line, count=1)
        # Match the timestamp and it is an empty line
        if lineNoTS in ['\n', '\r\n']:
            recovContxt = True
        else:
            recovContxt = False

    newfile.write(lastline)
    lastline = line
    lastlineTS = currlineTS

# write the last line of the newfile
newfile.write(lastline)

rawfile.close()
newfile.close()