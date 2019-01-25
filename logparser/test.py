import re
from datetime import datetime
import os
import pandas as pd
#import numpy as np

teststrin = re.sub(' +', '\\\\s+', "123 abc  ABC")

m = re.search(r'(?<=[^A-Za-z0-9])(\-?\+?\d+)(?=[^A-Za-z0-9])|[0-9]+$', '#$--++123@#456')
print(m.group(0))

print(teststrin)

"""
print(datetime.now())

currentfiledir = os.path.dirname(__file__)
print(currentfiledir)
parentddir = os.path.abspath(os.path.join(currentfiledir, os.path.pardir))
print(type(parentddir))
"""

log_format = '<Date> <Time> <Pid> <Level> <Component>: <Content>'
headers = []
splitters = re.split(r'(<[^<>]+>)', log_format)
regex = ''
for k in range(len(splitters)):
    if k % 2 == 0:
        splitter = re.sub(' +', '\\\\s+', splitters[k])
        #print(splitter)
        regex += splitter
    else:
        header = splitters[k].strip('<').strip('>')
        print(header)
        regex += '(?P<%s>.*?)' % header
        headers.append(header)

print(regex)
print(headers)

m1 = re.search('(?P<Content>.*?)', '')
print(m1.group(0))

log_messages = []
a1 = [1, 2, 3]
a2 = [4, 5, 6]
a3 = [7, 8, 9]
a4 = [10, 11, 12]

log_messages.append(a1)
log_messages.append(a2)
log_messages.append(a3)
log_messages.append(a4)
print(log_messages)

df = pd.DataFrame(log_messages,columns=['Level', 'Component', 'Content'])
df.insert(0, 'LineId', None)
df['LineId'] = [i + 1 for i in range(4)]
print(type(df))
print(type(df['LineId']))

for dummy, line in df.iterrows():
    print(type(line['Content']))

print(len(df))

tmpDict = {'a':1, 'b':2, 'c':3}
seqLen = 'c'
if seqLen in tmpDict:
    print(seqLen)

s = 'res12'
any = any(char.isdigit() for char in s)
print(any)