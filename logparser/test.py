import re
from datetime import datetime
import os
#import pandas as pd
#import numpy as np

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
#file       = open(parentdir + '/logs/test.txt', 'r')
#newfile    = open(parentdir + '/logs/test_tmp.txt', 'w')


teststrin = re.sub(' +', '\\\\s+', "123 abc  ABC", count=0)

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

#log_format = '<Date> <Time> <Pid> <Level> <Component>: <Content>'
log_format = '<Content>'
headers = []
splitters = re.split(r'(<[^<>]+>)', log_format)
print(splitters)
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

"""
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
print(df['LineId'])

df['LineId'] = ['a', 'b', 'c', 'd']
print(df['LineId'])

#No df.insert() for the new column. Work!
df['test'] = ['a', 'a', 'c', 'd']
print(df['test'])
print(df['test'].value_counts())

for dummy, line in df.iterrows():
    print(type(line['Content']))

print(len(df))
"""

"""
tmpDict = {'a':1, 'b':2, 'c':3}
seqLen = 'c'
if seqLen in tmpDict:
    print(seqLen)

s = 'res12'
any = any(char.isdigit() for char in s)
print(any)

for i, j in zip([1,2,3],['a','b','c']):
    print(i, j)

a = "i am a bo"
b = "i am a boy"
if ' '.join(a) == ' '.join(b):
    print(True)
print(' '.join(a))
"""

a = [(5, 2), (4, 1), (9, 10), (13, -3)]
a.sort(key=lambda x: x[0])

print(a)

str1 = "    8   149    66     0x2      20   63.700 - 78.450        0     5      y"
str2 = str1.split(None, 8)
#print(str1.strip())
print(str2[8][6])
str3 = 'testme' + ', rxid ' + str2[0] + ', dcid ' \
        + str2[1] + '\n'
print(str3)

aa = 0
if aa not in [1, 2]:
    print('hello')
