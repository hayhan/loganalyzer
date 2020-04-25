#!/usr/bin/env python3
"""
Description : This file formats the original CM/DOCSIS log
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
#import sys
from datetime import datetime

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
#sys.path.append(parentdir)

#from tools import helper

"""
Process the train data or test data
"""
# Read the config file to decide
with open(parentdir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conline = confile.readline().strip()
    if conline == 'TRAINING=1':
        TRAINING = True
        datatype = 'train'
    else:
        TRAINING = False
        datatype = 'test'

if TRAINING:
    raw_file_loc  = parentdir + '/logs/train.txt'
    new_file_loc  = parentdir + '/logs/train_new.txt'
    norm_file_loc = parentdir + '/logs/train_norm.txt'
    results_loc   = parentdir + '/results/train'
    label_vector_file = results_loc + '/train_norm.txt_labels.csv'
else:
    raw_file_loc  = parentdir + '/logs/test.txt'
    new_file_loc  = parentdir + '/logs/test_new.txt'
    norm_file_loc = parentdir + '/logs/test_norm.txt'
    results_loc   = parentdir + '/results/test'
    label_vector_file = results_loc + '/test_norm.txt_labels.csv'

# Create results/ and sub-dir train/ and test/ if not exist
if not os.path.exists(parentdir+'/results'):
    os.mkdir(parentdir+'/results')

if not os.path.exists(results_loc):
    os.mkdir(results_loc)

"""
The original log usually comes from serial console tools like SecureCRT
in Windows and the text file encoding is probably utf-8 (with BOM).
https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8

To let python skip the BOM when decoding the file, use utf-8-sig codec.
https://docs.python.org/3/library/codecs.html
"""
file       = open(raw_file_loc, 'r', encoding='utf-8-sig')
newfile    = open(new_file_loc, 'w')
normfile   = open(norm_file_loc, 'w')

"""
Definitions:
primary line - no space proceeded
nested line  - one or more spaces proceeded
empty line   - LF or CRLF only in one line
"""

"""
Patterns for removing timestamp, console prompt and others
"""
# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738]. Label is also considered.
strPattern0 = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)\.(\d{3})|24:00:00\.000)\] (abn: )?')
# The pattern for CM console prompts
strPattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
# The pattern for the timestamp added by BFC, e.g. [00:00:35 01/01/1970], [11/21/2018 14:49:32]
strPattern2 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{2}/\d{2}/\d{4}\] ')
strPattern3 = re.compile(r'\[\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)\] ')
# The pattern for the timestamp added by others, e.g. 01/01/1970 00:00:19
strPattern4 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')
# The pattern for the tag of thread
strPattern5 = re.compile(r'\[[a-z ]*\] ', re.IGNORECASE)
strPattern6 = re.compile(r'\+{3} ')

strPatterns = [
    strPattern1, strPattern2, strPattern3,
    strPattern4, strPattern5, strPattern6
]

# decide if we need reserve the main timestamp: strPattern0 in the norm file
reserveTS = True

"""
Patterns for specific lines which I want to remove
"""
sLinePattern0 = re.compile(r'\*')
sLinePattern1 = re.compile(r'\+{10}')
sLinePattern2 = re.compile(r'Received DBC-REQ \(trans. id\=')
sLinePattern3 = re.compile(r'RCC->')
sLinePattern4 = re.compile(r'TCC->')
sLinePattern5 = re.compile(r'\d')
sLinePattern6 = re.compile(r'Readback Test pkt\:')
sLinePattern7 = re.compile(r'DHCPc\:  Timed out waiting for offers for lease')
sLinePattern8 = re.compile(r'ng...')
sLinePattern9 = re.compile(r'fUsSetsState = ')

sLinePatterns = [
    sLinePattern0,
    sLinePattern1,
    sLinePattern2,
    sLinePattern3,
    sLinePattern4,
    sLinePattern5,
    sLinePattern6,
    sLinePattern7,
    sLinePattern8,
    sLinePattern9
]

"""
Patterns for removing Table headers
"""
title0  = re.compile(r' *Trimmed Candidate Downstream Service Group')
title1  = re.compile(r' *sgid +size +member')
title2  = re.compile(r' *Downstream Active Channel Settings')
title3  = re.compile(r' *dcid +type +frequency')
title4  = re.compile(r' *Upstream Active Channel Settings')
title5  = re.compile(r' *ucid +rpt enable')
title6  = re.compile(r' *BcmCmUsTargetMset \(a.k.a. usable UCDs')
title7  = re.compile(r' *us +config')
title8  = re.compile(r' *phy +change')
title9  = re.compile(r' *type +ucid +dcid +count')
title10 = re.compile(r' *REG-RSP-MP Summary:')
title11 = re.compile(r' *TCC commands->')
title12 = re.compile(r' *ucid +action +ranging strategy')
title13 = re.compile(r' *Service Flow settings->')
title14 = re.compile(r' *sfid +sid +ucids')
title15 = re.compile(r' *DSID settings->')
title16 = re.compile(r' *dsid +action +reseq')
title17 = re.compile(r' *Active Downstream Channel Diagnostics')
title18 = re.compile(r' *rx id +dcid +freq')
title19 = re.compile(r' *plc +prfA')
title20 = re.compile(r' *Active Upstream Channels:')
title21 = re.compile(r' *rng +pwr')
title22 = re.compile(r' *txid +ucid +dcid +sid')

titlePatterns = [
    title0,  title1,  title2,  title3,  title4,  title5,  title6,  title7,
    title8,  title9,  title10, title11, title12, title13, title14, title15,
    title16, title17, title18, title19, title20, title21, title22
]

"""
Pattern for nested line
"""
nestedLinePattern = re.compile(r' +')

"""
Patterns for specific primary lines which I want to indent them
"""
sPrimaryLinePattern0 = re.compile(r'Assigned OFDMA Data Profile IUCs')
sPrimaryLinePattern1 = re.compile(r'fDestSingleTxTargetUsChanId')
sPrimaryLinePattern2 = re.compile(r'fTmT4NoUnicastRngOpStdMlsec')

sPrimaryLinePatterns = [
    sPrimaryLinePattern0,
    sPrimaryLinePattern1,
    sPrimaryLinePattern2
]

"""
Patterns for specific lines which I want to convert them as primary
"""
sNestedLinePattern0 = re.compile(r' +DOWNSTREAM STATUS')
sNestedLinePattern1 = re.compile(r' +CM Upstream channel info')
sNestedLinePattern2 = re.compile(r' +Receive Channel Config\:')

sNestedLinePatterns = [
    sNestedLinePattern0,
    sNestedLinePattern1,
    sNestedLinePattern2
]

"""
Patterns for nested lines (exceptions) which I do not want to make them as primary
"""
eNestedLinePattern0 = re.compile(r' +Ranging state info:')

eNestedLinePatterns = [
    eNestedLinePattern0
]

"""
Patterns for specific whole multi-line log which I want to remove entirely
"""
wMultiLineRmPattern0 = re.compile(r'Configured O-INIT-RNG-REQ \:')

wMultiLineRmPatterns = [
    wMultiLineRmPattern0
]

"""
Patterns for other specific lines
"""
# DS/US channel status tables
dsChStatTablePattern = re.compile(r'Active Downstream Channel Diagnostics\:')
usChStatTablePattern = re.compile(r'Active Upstream Channels\:')
# Common table
commonTablePattern = re.compile(r' *----')
# Initial ranging block for each UCID
initRangePattern = re.compile(r'== Beginning initial ranging for Docsis UCID')
inMultiLineInitRangeEnd1 = re.compile(r'Using clamped minimum transmit power')
inMultiLineInitRangeEnd2 = re.compile(r'Using bottom of DRW initial upstream power')
inMultiLineInitRangeEnd3 = re.compile(r'Using per transmitter stored initial upstream power')
# Assign token something like ABC=xyz or ABC==xyz
assignTokenPattern = re.compile(r'=(?=[^= \r\n])')
# Cpp class token like ABC::Xyz:
cppClassPattern = re.compile(r'\:\:(?=[A-Z][a-z0-9]+)')
# Split 'ABC;DEF' to 'ABC; DEF'
semicolonPattern = re.compile(r';(?! )')
# Change something like (xx), [xx], ..., to ( xx ), [ xx ], ...
bracketPattern1 = re.compile(r'\((?=(\w|[-+]))')
bracketPattern2 = re.compile(r'(?<=\w)\)')
bracketPattern3 = re.compile(r'\[(?=(\w|[-+]))')
bracketPattern4 = re.compile(r'(?<=\w)\]')
bracketPattern5 = re.compile(r'\d+(?=(ms))')
#bracketPattern6 = re.compile(r'(?<=\.\.)\d')

"""
Variables initialization
"""
inDsChStatTable = False
inUsChStatTable = False
tableMessed = False
dsTableEntryProcessed = False
lastLineMessed = False
inTable = False
inMultiLineInitRange = False
inMultiLineRemove = False
lastLineEmpty = False
sccvEmptyLineCnt = 0

"""
01) Remove timestamps, console prompts, tables, empty lines
02) Format DS/US channel status tables
03) Remove some tables which are useless
04) Format initial ranging block to one line log
05) Indent some specific lines in multi-line log
06) Remove empty lines
07) Convert an nested line as primary if two more empty lines proceeded
08) Convert some specific lines as primary
09) Remove specific whole multi-line log
10) Split some tokens
"""
print("Pre-processing the raw {0} dataset ...".format(datatype))
parse_st = datetime.now()
#linesLst = file.readlines()
#rawsize = len(linesLst)

#for idx, line in enumerate(linesLst):
for line in file:

    # Update the progress bar
    #helper.printProgressBar(idx+1, rawsize, prefix='Progress:')
    """
    Remove the unwanted strings which include some kind of timestamps, console prompts and etc.
    """
    # Save the main timestamp if it exists. The newline does not contain the main
    # timestamp before write it back to a new file. Train label is also considered
    # in this pattern. Add it back along with main timestamp at the end.
    matchTS = strPattern0.match(line)
    if matchTS:
        currentLineTS = matchTS.group(0)
        newline = strPattern0.sub('', line, count=1)
    else:
        newline = line

    """
    No main timestamp and train label at the begining of each line in the remaining of the loop
    """
    # Remove remaining timestamp, console prompt and others
    for pattern in strPatterns:
        newline = pattern.sub('', newline, count=1)

    # Remove the line if the timestamp appears in the middle because of code bug w/o endl.
    if strPattern2.search(newline):
        # Update for the next line
        lastLineEmpty = False
        continue

    # Remove line starting with specific patterns
    goNextLine = False
    for pattern in sLinePatterns:
        match = pattern.match(newline)
        if match:
            goNextLine = True
            break
    if goNextLine == True:
        # Update for the next line
        lastLineEmpty = False
        continue

    # Format DS channel status table
    #
    # Active Downstream Channel Diagnostics:
    #
    #   rx id  dcid    freq, hz  qam  fec   snr, dB   power, dBmV  modulation
    #                            plc  prfA
    #   -----  ----  ----------  ---  ---  ---------  -----------  ----------
    #       0*    1   300000000   y    y          35            3       Qam64
    #       1     2   308000000   y    y          34            4      Qam256
    #      32    66   698000000   y    y          35            1    OFDM PLC
    #
    match = dsChStatTablePattern.match(newline)
    if match:
        inDsChStatTable = True
    elif inDsChStatTable and inTable:
        if (not nestedLinePattern.match(newline)) and (newline not in ['\n', '\r\n']):
            # The table is messed by printings from other thread if we run into here
            # The normal DS channel status row should be nested by default. The messed
            # table might have empty lines in the middle of table
            tableMessed = True
            # Remove this line here, do not leave it to the "Remove table block"
            # Update for the next line
            lastLineEmpty = False
            continue
        elif newline in ['\n', '\r\n'] and dsTableEntryProcessed and (not lastLineMessed):
            # Suppose table ended with empty line but need also consider the case of
            # messed table. The 'dsTableEntryProcessed', 'lastLineMessed' and 'tableMessed'
            # are used here to process the messed table case.
            # Leave reset of 'inTable' to the "Remove table block"
            inDsChStatTable = False
            tableMessed = False
            dsTableEntryProcessed = False
        elif newline not in ['\n', '\r\n']:
            # The real table row, that is, nested line
            dsTableEntryProcessed = True
            # Convert current line to new ds format
            # DS channel status, rxid 0, dcid 1, freq 300000000, qam y, fec y, snr 35, power 3, mod Qam256
            lineList = newline.split(None, 7)
            if tableMessed:
                # Need consider the last colomn of DS channel status, aka. lineList[7]
                if lineList[7] not in ['Qam64\n', 'Qam256\n', 'OFDM PLC\n', 'Qam64\r\n', 'Qam256\r\n', 'OFDM PLC\r\n']:
                    # Current line is messed and the last colomn might be concatednated by
                    # other thread printings inadvertently and the next line will be empty
                    # See example of the DS messed table in test.003.txt
                    # Update lastLineMessed for next line processing
                    lastLineMessed = True
                    if lineList[7][3] == '6':       # Qam64
                        lineList[7] = 'Qam64\n'
                    elif lineList[7][3] == '2':     # Q256
                        lineList[7] = 'Qam256\n'
                    else:
                        lineList[7] = 'OFDM PLC\n'  # OFDM PLC
                else:
                    lastLineMessed = False

            if lineList[7][0] == 'O':
                # Keep the OFDM channel status log length as same as QAM channel
                # Then they will share the same log template after clustering
                lineList[7] = 'OFDM_PLC\n'  # OFDM PLC

            newline = 'DS channel status' + ' rxid ' + lineList[0] + ' dcid ' + lineList[1] + \
                      ' freq ' + lineList[2] + ' qam ' + lineList[3] + ' fec ' + lineList[4] + \
                      ' snr ' + lineList[5] + ' power ' + lineList[6] + ' mod ' + lineList[7]

    # Format US channel status table
    #
    # Active Upstream Channels:
    #
    #                     rng     pwr        frequency     symbols   phy  ok tx
    #  txid  ucid  dcid   sid     dBmv          MHz          sec    type  data?
    #  ----  ----  ----  ------  -----    ---------------  -------  ----  -----
    #     0   101     1     0x2      18             9.000  5120000     3      y
    #     1   102     1     0x2      18            15.400  5120000     3      y
    #     8   149     1     0x2      18   63.700 - 78.450        0     5      y
    #
    match = usChStatTablePattern.match(newline)
    if match:
        inUsChStatTable = True
    elif inUsChStatTable and inTable:
        if newline in ['\n', '\r\n']:
            # Suppose table ended with empty line
            # Leave reset of inTable to the remove table block
            inUsChStatTable = False
        else:
            # Convert current line to new us format
            # US channel status, txid 0, ucid 101, dcid 1, rngsid 0x2, power 18, freq_start 9.000, freq_end 9.000, symrate 5120000, phytype 3, txdata y
            lineList = newline.split(None, 8)
            if lineList[6] == '-':
                # This line is for OFDMA channel, so split it again
                lineList = newline.split(None, 10)
                newline = 'US channel status' + ' txid ' + lineList[0] + ' ucid ' + lineList[1] + \
                          ' dcid ' + lineList[2] + ' rngsid ' + lineList[3] + ' power ' + lineList[4] + \
                          ' freqstart ' + lineList[5] + ' freqend ' +lineList[7] + \
                          ' symrate ' + lineList[8] + ' phytype ' + lineList[9] + \
                          ' txdata ' + lineList[10]
            else:
                # For SC-QAM channels
                newline = 'US channel status' + ' txid ' + lineList[0] + ' ucid ' + lineList[1] + \
                          ' dcid ' + lineList[2] + ' rngsid ' + lineList[3] + ' power ' + lineList[4] + \
                          ' freqstart ' + lineList[5] + ' freqend ' +lineList[5] + \
                          ' symrate ' + lineList[6] + ' phytype ' + lineList[7] + \
                          ' txdata ' + lineList[8]

    # Remove table block
    # The line starting with "----", " ----" or "  ----"
    match = commonTablePattern.match(newline)
    if match:
        inTable = True
        # Update for the next line
        lastLineEmpty = False
        continue
    elif inTable == True:
        if newline in ['\n', '\r\n']:
            # Suppose table ended with empty line
            if (not inDsChStatTable) or (inDsChStatTable and dsTableEntryProcessed and (not lastLineMessed)):
                inTable = False
        elif not (inDsChStatTable or inUsChStatTable):
            # Still table line, remove it
            # Update for the next line
            lastLineEmpty = False
            continue

    # Remove specific table title line
    goNextLine = False
    for pattern in titlePatterns:
        match = pattern.match(newline)
        if match:
            goNextLine = True
            break
    if goNextLine == True:
        # Update for the next line
        lastLineEmpty = False
        continue

    # Indent lines as multi-line log for initial ranging
    match = initRangePattern.match(newline)
    if match:
        inMultiLineInitRange = True
    elif inMultiLineInitRange:
        if inMultiLineInitRangeEnd1.match(newline) or inMultiLineInitRangeEnd2.match(newline) \
            or inMultiLineInitRangeEnd3.match(newline):
            # Suppose multi-line log ended with special lines
            newline = ' ' + newline
            inMultiLineInitRange = False
        else:
            # Still multi-line, indent it, say add a space at the start
            newline = ' ' + newline

    # Indent some specific lines
    for pattern in sPrimaryLinePatterns:
        match = pattern.match(newline)
        if match:
            # Indent this line
            newline = ' ' + newline
            break

    # It is time to remove empty line
    if newline in ['\n', '\r\n']:
        if lastLineEmpty == False:
            sccvEmptyLineCnt = 1
        else:
            sccvEmptyLineCnt += 1

        # Update lastLineEmpty for the next line processing
        lastLineEmpty = True
        continue

    # Convert a nested line as primary if two more empty lines proceeded
    if nestedLinePattern.match(newline):
        if (lastLineEmpty == True) and (sccvEmptyLineCnt >= 2):
            # Try to see if there are any exceptions
            noException = True
            for pattern in eNestedLinePatterns:
                if pattern.match(newline):
                    noException = False
                    break
            if noException:
                newline = newline.lstrip()

    # Convert some specific nested lines as primary
    for pattern in sNestedLinePatterns:
        match = pattern.match(newline)
        if match:
            newline = newline.lstrip()
            break

    # Remove specific whole multi-line log
    foundPattern = False
    for pattern in wMultiLineRmPatterns:
        match = pattern.match(newline)
        if match:
            foundPattern = True
            break
    if foundPattern:
        inMultiLineRemove = True
        # Delete current line
        # Update for the next line
        lastLineEmpty = False
        continue
    elif inMultiLineRemove:
        if not nestedLinePattern.match(newline):
            inMultiLineRemove = False
        else:
            # Delete current line
            # Update for the next line
            lastLineEmpty = False
            continue

    # Split assignment token something like ABC=xyz to ABC= xyz
    newline = assignTokenPattern.sub('= ', newline)

    # Split class token like ABC::Xyz: to ABC:: Xyz:
    newline = cppClassPattern.sub(':: ', newline)

    # Split 'ABC;DEF' to 'ABC; DEF'
    newline = semicolonPattern.sub('; ', newline)

    # Change something like (xx), [xx], ..., to ( xx ), [ xx ], ...
    newline = bracketPattern1.sub('( ', newline)
    newline = bracketPattern2.sub(' )', newline)
    newline = bracketPattern3.sub('[ ', newline)
    newline = bracketPattern4.sub(' ]', newline)

    m = bracketPattern5.search(newline)
    if m:
        substring = m.group(0)
        newline = bracketPattern5.sub(substring+' ', newline)

    """
    m = bracketPattern6.search(newline)
    if m:
        substring = m.group(0)
        newline = bracketPattern6.sub(' '+substring, newline)
    """

    # Update lastLineEmpty for the next line processing
    lastLineEmpty = False

    # Write current line to a new file with the timestamp if it exists
    if reserveTS and matchTS:
        newline = currentLineTS + newline
    newfile.write(newline)

file.close()
newfile.close()
print('Purge costs {!s}\n'.format(datetime.now()-parse_st))


"""
Convert multi-line log to one-line format
"""

# Scan the new generated newfile
newfile    = open(new_file_loc, 'r')
normfile   = open(norm_file_loc, 'w')

"""
Variables initialization
"""
# The lastLine is initialized as empty w/o LF or CRLF
lastLine = ''
lastLinTS = ''

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
Generate the label vector from norm file and remove the labels in norm file
ToDo: optimize for test dataset if no validation is needed
"""
import pandas as pd

# Label pattern
labelPattern = re.compile(r'abn: ')

label_messages = []
linecount = 0
norm_logs = []

with open(norm_file_loc, 'r') as fin:
    for line in fin.readlines():
        try:
            match = labelPattern.search(line, 24, 29)
            if match:
                label_messages.append('a')
                newline = labelPattern.sub('', line, count=1)
            else:
                label_messages.append('-')
                newline = line

            linecount += 1
            # Label is removed
            norm_logs.append(newline)
        except Exception:
            pass

logdf = pd.DataFrame(label_messages, columns=['Label'])
logdf.insert(0, 'LineId', None)
logdf['LineId'] = [i + 1 for i in range(linecount)]
# Save the label vector to results/train or results/test
logdf.to_csv(label_vector_file, index=False)

# Overwrite the old norm file with contents that labels are removed
with open(norm_file_loc, 'w+') as fin:
    fin.writelines(norm_logs)