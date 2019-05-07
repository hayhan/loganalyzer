"""
Description : This file does regrex, paramter settings and then calls the parsing core
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""
#!/usr/bin/env python3
import os
import re
from Drain_DOCSIS import LogParser

"""
Input and output files
"""
curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
input_dir  = parentdir + '/logs/'       # The input directory of log file
output_dir = parentdir + '/results/'    # The output directory of parsing results
log_file   = 'test_norm.txt'            # The input log file name
log_format = '<Content>'                # DOCSIS log format

"""
Regular expression list for optional preprocessing (can be empty [])
"""
# The libc ctime format
regexPattern0 = re.compile(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) (([0-2]\d)|(3[0-1])) (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{4}')
# MAC Address
regexPattern1 = re.compile(r'([A-Fa-f0-9]+\:){5}[A-Fa-f0-9]+')
# IPv4 Address
regexPattern2 = re.compile(r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)')
# IPv6 Address from https://gist.github.com/mnordhoff/2213179
# A more elegant rex can be found at https://gist.github.com/dfee/6ed3a4b05cfe7a6faf40a2102408d5d8
regexPattern3 = re.compile(r' (?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)(/\d{1,3})?')
# Numbers including hex, decimal and integer
#r'(?<=[^A-Za-z0-9])(\-?\+?\d+)(?=[^A-Za-z0-9])|[0-9]+$|0x[A-Fa-f0-9]+'
regexPattern4 = re.compile(r'0x[A-Fa-f0-9]+|(?<=[^A-Za-z0-9])(\-?\+?\d+\.?(\d+)?\*?)')

regex = [
    regexPattern0,
    regexPattern1,
    regexPattern2,
    regexPattern3,
    regexPattern4
]

"""
Regular expression dict for adaptively changing of depth to avoid over-parsing.

The smallest index (count from 1) for the varialbe token is depth-2. e.g. if we
want to make the 1st token to be varialbe, we can set depth to 3.

I want to resolve the over-parsing issue like below. If use depth=4, the 'tim='
will be thought as a variable. To avoid this, I set the smallest index of variable
to 6=8-2, aka. starting from 1491, then 'tim=' will not be replaced with '<*>'.

Ex.
      RNG-RSP UsChanId= 102  Adj: tim= 1491  Stat= Continue

if depth is 4, the smallest index of var is 4-2=2, the parsing result will be
  --> RNG-RSP UsChanId= <*> Adj: <*> <*> Stat= <*>

if depth is 8, the smallest index of var is 8-2=6, the parsing result will be
  --> RNG-RSP UsChanId= <*> Adj: tim= <*> Stat= <*>

Note: Actually this method has protential problems that these specific logs will
      have different depths for the leaf nodes. For the same length log that does
      not match the regrex might have running errors. We need use domain knowledge
      here to avoid the protential problems happening.
"""
depthPattern0 = re.compile(r'RNG-RSP UsChanId= \d+  Adj\:')
depthPattern1 = re.compile(r'Telling application we lost lock on')

depthPatterns = {
    depthPattern0: 6,  # 8-2
    depthPattern1: 8   # 10-2
}


"""
Other parameters
"""
st         = 0.5  # Similarity threshold
depth      = 4    # Depth of all leaf nodes

"""
Let us generate templates now
"""
parser = LogParser(log_format, indir=input_dir, outdir=output_dir,  depth=depth, st=st, rex=regex, depthPatterns=depthPatterns)
parser.parse(log_file)