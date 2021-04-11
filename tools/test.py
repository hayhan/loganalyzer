import re
from datetime import datetime
import os
import sys
import pandas as pd
import numpy as np
from sklearn.utils import shuffle

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
#file       = open(parentdir + '/logs/cm/test.txt', 'r')
#newfile    = open(parentdir + '/logs/cm/test_tmp.txt', 'w')

teststrin0 = re.sub(r'Assigned Data', '',
                    '[16:06:51:140]Assigned Data OFDMA Data Profile IUCs 123456', count=1)
print(teststrin0)

teststrin = re.sub(' +', '\\\\s+', "123 abc  ABC", count=0)
print(teststrin)

m = re.search(r'(?<=[^A-Za-z0-9])(\-?\+?\d+)(?=[^A-Za-z0-9])|[0-9]+$', '0x56')
print(m.group(0))

#line = "P1.6hi P=1.6hi P6hi; CM-QOS=1.1; CM-VER=3.1; ipv6; D31; D31 5x; ..23; US:(0 MHz..204 MHz) DS:(258 MHz..1218 MHz); fMdDsSgId=0x7f (127)"
line = "BcmBfcProcessCvc::CmCodeVerificationCertificate::ParseAndValidate:  (Process CVC) ERROR - Failed on rsaDecryptSignature, status=0x1, Certificate::ParseAndValidate:  (11qq/c CVC) "
#currentRex = r'\d+|\d+\.\d+'
#currentRex = r'(\(\d+\.?(\d+)?-\d+\.?(\d+)?\) )+'  # Numbers
#currentRex = r'[A-Fa-f0-9]{2}'
#currentRex = r'(\(\d+\.?(\d+)?-\d+\.?(\d+)?\) )+|( [A-Fa-f0-9]+){2,}|0x[A-Fa-f0-9]+|(?<=[^A-Za-z0-9])((\[ )?\-?\+?\d+\.?(\d+)?\*?( \])?)'
#currentRex1 = r'([A-Fa-f0-9]+\:){5}[A-Fa-f0-9]+'
#currentRex3 = re.compile(
#    r'( \( \d+\.?(\d+)?-\d+\.?(\d+)? \))+'
#    r'|( \d+){2,}'
#    r'|0x[A-Fa-f0-9]+'
#    r'|(?<=[^A-Za-z0-9\.])(\-?\+?\d+\.?(\d+)?\*?)'
#    r'|(?<=\.\.)(\d+)'
#)
currentRex4 = re.compile(r'(?<=:  )\([a-zA-Z0-9/ ]+\) ')

#line = re.sub(currentRex, '<*>', "Readback Test pkt: 0x2 =-18dB 300.123 10.156 -19dB -20.7890 30.111 dcid=1, ucid12 dcid11 ver=3.1; ucid22, 0x33")
#line = re.sub(currentRex, '<*>', "RNsG-RSP s UsChanId = 149  Adj: tim=12496  Stat=Continue")
#line = re.sub(currentRex, ' <*>', "CM-STATUS [ 12 ] trans= 1 4 ffevent= 5 (kCmEvDsPhyLockRescue)  param type= 4 (dcid)  param values= [ 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 ] ttt: 18 de 33 93 00 03 00 01 00 10 18 de 33 93 ")
#line = re.sub(currentRex1, ' <*>', "Logging event: CM-STATUS message sent. Event Type Code: 5; Chan ID: 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32; DSID: N/A; MAC Addr: N/A; OFDM/OFDMA Profile ID: N/A.; CM-MAC= 00:10:18:de:33:93; CMTS-MAC= 00:80:42:42:20:9e; CM-QOS= 1.1; CM-VER= 3.1; ")
#line = re.sub(currentRex2, ' <*>', line)
#line = re.sub(currentRex3, ' <*>', line)
line = currentRex4.sub('', line, count=0)
print(line)
sys.exit(0)

# IPv6 Address
ipRex = r' (?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)(/\d{1,3})?'
#ipRex = '^(?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)%25(?:[A-Za-z0-9\\-._~]|%[0-9A-Fa-f]{2})+$'
#ipRex = '^(?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)(?:%25(?:[A-Za-z0-9\\-._~]|%[0-9A-Fa-f]{2})+)?$'

#line = re.sub(ipRex, '<*>', "fe80::210:18ff:fede:b518/64")
line = re.sub(ipRex, ' <*>', "BcmEcosIpHalIf::RemoveIpv6Address: (IP Stack1 HalIf) ERROR - Failed to remove IPv6 address fe80::210:18ff:fede:b518/64 from the stack!")
print(line)

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
        # print(splitter)
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
# print(str1.strip())
print(str2[8][6])
str3 = 'testme' + ', rxid ' + str2[0] + ', dcid ' \
    + str2[1] + '\n'
print(str3)

aa = 0
if aa not in [1, 2]:
    print('hello')

t1 = pd.to_datetime("[20190719-08:58:23.748]", format="[%Y%m%d-%H:%M:%S.%f]")
t2 = pd.to_datetime("[20190719-09:03:23.389]", format="[%Y%m%d-%H:%M:%S.%f]")
print(t2-t1)
print((t2-t1).total_seconds())

"""
data_df1 = pd.read_csv(parentdir+'/results/test_norm.txt_labeled.csv', usecols=['Label'])
data_df1['Label'] = (data_df1['Label'] != '-').astype(int)

data_df2 = pd.read_csv(parentdir+'/results/test_norm.txt_structured.csv', usecols=['Time', 'EventId'])
data_df2['Time'] = pd.to_datetime(data_df2['Time'], format="[%Y%m%d-%H:%M:%S.%f]")
data_df2['Ms_Elapsed'] = ((data_df2['Time']-data_df2['Time'][0]).dt.total_seconds()*1000).astype(int)

data_df2['Label'] = data_df1['Label']
raw_data = data_df2[['Label','Ms_Elapsed']].values

event_mapping_data = data_df2['EventId'].values

#print(type(data_df2))
print(raw_data)
print(event_mapping_data)
print('The number of anomaly logs is %d, but it requires further processing' % sum(raw_data[:, 0]))
"""
listtmp = ['a', 'b', 'c', 'd', 'e']
newlist = shuffle(listtmp)
#indexes = shuffle(np.arange(5))
# print(indexes)
# print(newlist)
# print(listtmp.index('b'))
tmpchar = 'f'
try:
    idx = listtmp.index(tmpchar)
    print(idx)
except:
    print('Warning: %s is not in the list' % tmpchar)

with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    line = confile.readline().strip()
    print(line)
    if line == 'TRAINING=1':
        print('it is 1')

line = 'CM-STATUS Stat= Abort'
testrex = re.compile(r'Stat= (Continue|Success|Abort)')
newline = testrex.sub('matched', line)
print(newline)

event_id_templates_old = ['a', '0', 'x', 'd', '0', 'f']
event_id_templates     = ['a', 'b', 'c', 'd', 'e', 'fg']
event_id_zero = [event_id_templates[idx] for idx, tid in enumerate(event_id_templates_old) if tid == '0']
if len(event_id_zero):
    print(event_id_zero)

event_id_old_nonzero = [event_id_templates[idx] \
                        for idx, (tidOld, tidNew) \
                        in enumerate(zip(event_id_templates_old, event_id_templates)) \
                        if tidOld != '0' and tidOld != tidNew]
print(event_id_old_nonzero)

# verify main "timestamp + abn: "
strPattern0 = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)\.(\d{3})|24:00:00\.000)\] (abn: )?')
line = "[20190719-09:12:01.910] abn: [09:16:21 07/19/2019] [CmDocsisCtlThread] BcmCmDocsisCtlThread"
matchTS = strPattern0.match(line)
if matchTS:
    currentLineTS = matchTS.group(0)
    newline = strPattern0.sub('', line, count=1)
print(newline)

################
"""
eidx_logs = [99, 98, 97, 96, 95, 94, 93, 92, 91, 90, \
            89, 88, 87, 86, 85, 84, 83, 82, 81, 80]
labels = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, \
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
results_lst = []
logsnum = len(eidx_logs)
i = 0
while (i + 5) < logsnum:
    sequence = eidx_logs[i: i + 5]
    results_lst.append([i, sequence, eidx_logs[i + 5], labels[i + 5]])
    i += 1
print(results_lst)

results_df = pd.DataFrame(results_lst, columns=["SeqId", "EventSeq", "Target", "Label"])
results_dict = {"SeqId": results_df["SeqId"].to_numpy(dtype='int32'),
                "EventSeq": np.array(results_df["EventSeq"].tolist(), dtype='int32'),
                "Target": results_df["Target"].to_numpy(dtype='int32'),
                "Label": results_df["Label"].to_numpy(dtype='int32')}
print(results_dict)
"""
##############defferent between tensor.clone() and tensor.detach()#################
# https://discuss.pytorch.org/t/clone-and-detach-in-v0-4-0/16861/17
# https://discuss.pytorch.org/t/difference-between-detach-clone-and-clone-detach/34173/5
import torch

x = torch.tensor(([1.0]), requires_grad=True)
y = x**2
z = 2*y
w = z**3

# This is the subpath
# Do not use detach()
"""
#p = z # no copy, so p and z share the same tensor
p = z.clone() # clone() makes a copy
print(id(z), id(p))
q = torch.tensor(([2.0]), requires_grad=True)
pq = p*q
pq.backward(retain_graph=True)
"""

# detach it, so the gradient w.r.t `p` does not effect `z`!
"""
p = z.detach() # detach(), pytorch doc says they share same storage
print(z.addr, p.addr) # but why the addresses are different?
q = torch.tensor(([2.]), requires_grad=True)
pq = p*q
pq.backward(retain_graph=True)
"""

w.backward()
print(x.grad)

##########################
def forward(aaa, *bbb):
    print(aaa)
    print(bbb[0])

forward('AAA', 'BBB', 'CCC')