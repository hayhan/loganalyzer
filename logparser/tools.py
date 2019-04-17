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
file       = open(parentdir + '/logs/HDFS_2k.log', 'r', encoding='utf-8-sig')
normfile   = open(parentdir + '/logs/test_norm.txt', 'w')

"""
Patterns for removing timestamp, console prompt and others
"""
# The pattern to remove non Content messages in the log
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