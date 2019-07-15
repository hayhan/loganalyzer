"""
Description : Tools
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

"""
The original log usually comes from serial console tools like SecureCRT
in Windows and the text file encoding is probably utf-8 (with BOM).
https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8

To let python skip the BOM when decoding the file, use utf-8-sig codec.
https://docs.python.org/3/library/codecs.html
"""

"""
file       = open(parentdir + '/logs/HDFS_2k.log', 'r', encoding='utf-8-sig')
normfile   = open(parentdir + '/logs/test_norm.txt', 'w')

# The pattern to remove non Content messages in the HDFS log
strPattern0 = re.compile(r'.*?\: ')

strPatterns = [
    strPattern0
]

for line in file:
    newline = line

    for pattern in strPatterns:
        newline = pattern.sub('', newline, count=1)

    normfile.write(newline)

file.close()
normfile.close()
"""

file       = open(parentdir + '/logs/test.txt', 'r', encoding='utf-8-sig')
tmpfile    = open(parentdir + '/logs/test_tmp.txt', 'w')

# The pattern to remove non Content messages in the HDFS log
strPattern0 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d):(\d{3})|24:00:00:000)\]')

for line in file:

    matchTS = strPattern0.match(line)
    timestamp = matchTS.group(0)
    newline = strPattern0.sub('', line, count=1)
    newline = timestamp + ' ' + newline
    tmpfile.write(newline)

file.close()
tmpfile.close()