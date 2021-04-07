"""
Description : Process the manually labeled logs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))


"""
Convert multi-line log to one-line format
"""

"""
Process the train data or test data
"""
# Read the config file to decide
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conline = confile.readline().strip()
    if conline == 'TRAINING=1':
        TRAINING = True
    else:
        TRAINING = False

if TRAINING:
    new_file_labeled_loc  = parentdir + '/logs/train_new_labeled.txt'
    norm_file_labeled_loc = parentdir + '/logs/train_norm_labeled.txt'
    label_vector_file_loc = parentdir + '/results/train/'
    norm_flie_name        = 'train_norm.txt'
else:
    new_file_labeled_loc  = parentdir + '/logs/test_new_labeled.txt'
    norm_file_labeled_loc = parentdir + '/logs/test_norm_labeled.txt'
    label_vector_file_loc = parentdir + '/results/test/'
    norm_flie_name        = 'test_norm.txt'

# Create results/ and sub-dir train/ and test/ if not exist
if not os.path.exists(parentdir+'/results'):
    os.mkdir(parentdir+'/results')

if not os.path.exists(label_vector_file_loc):
    os.mkdir(label_vector_file_loc)

# Scan the new generated newfile
newfile    = open(new_file_labeled_loc, 'r', encoding='utf-8')
normfile   = open(norm_file_labeled_loc, 'w', encoding='utf-8')

# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738]
strPattern0 = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)\.(\d{3})|24:00:00\.000)\] ')
# Pattern for nested line
nestedLinePattern = re.compile(r' +')

"""
Variables initialization
"""
# The lastLine is initialized as empty w/o LF or CRLF
lastLine = ''
lastLinTS = ''
reserveTS = True

"""
Concatenate nested line to its parent (primary) line
"""
for line in newfile:
    # Save timestamp if it exists
    matchTS = strPattern0.match(line)
    if matchTS:
        currentLineTS = matchTS.group(0)
        newline = strPattern0.sub('', line, count=1)
    else:
        newline = line

    if nestedLinePattern.match(newline):
        # Concatenate current line to lastLine. rstrip() will strip LF or CRLF too
        lastLine = lastLine.rstrip()
        lastLine += ', '
        lastLine += newline.lstrip()
    else:
        # If current is primary line, it means concatenating ends
        if reserveTS and matchTS and (lastLine != ''):
            lastLine = lastLineTS + lastLine
        normfile.write(lastLine)

        # Update last line parameters
        lastLine = newline
        if reserveTS and matchTS:
            lastLineTS = currentLineTS

# write the last line of the file
if reserveTS and matchTS and (lastLine != ''):
    lastLine = lastLineTS + lastLine
normfile.write(lastLine)

newfile.close()
normfile.close()

"""
Generate the label vector
"""
# Label pattern
labelPattern = re.compile(r'abn: ')

label_messages = []
linecount = 0
with open(norm_file_labeled_loc, 'r', encoding='utf-8') as fin:
    for line in fin.readlines():
        try:
            match = labelPattern.search(line, 24, 29)
            if match:
                label_messages.append('a')
            else:
                label_messages.append('-')
            linecount += 1
        except Exception:
            pass
logdf = pd.DataFrame(label_messages, columns=['Label'])
logdf.insert(0, 'LineId', None)
logdf['LineId'] = [i + 1 for i in range(linecount)]
logdf.to_csv(os.path.join(label_vector_file_loc, norm_flie_name + '_labeled.csv'), index=False)