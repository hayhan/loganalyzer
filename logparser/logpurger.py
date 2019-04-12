#!/usr/bin/env python3
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
file       = open(parentdir + '/logs/test.txt', 'r', encoding='utf-8-sig')
newfile    = open(parentdir + '/logs/test_new.txt', 'w')
normfile   = open(parentdir + '/logs/test_norm.txt', 'w')

"""
Definitions:
primary line - no space proceeded
nested line  - one or more spaces proceeded
empty line   - LF or CRLF only in one line
"""

"""
Patterns for removing timestamp, console prompt and others
"""
# The pattern for the timestamp added by console tool
strPattern0 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d):(\d{3})|24:00:00:000)\]')
# The pattern for CM console prompts
strPattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
# The pattern for the timestamp added by BFC
strPattern2 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{2}/\d{2}/\d{4}\] ')
strPattern3 = re.compile(r'\[\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)\] ')
# The pattern for the timestamp added by others
strPattern4 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')
# The pattern for the tag of thread
strPattern5 = re.compile(r'\[[a-z ]*\] ', re.IGNORECASE)
strPattern6 = re.compile(r'\+{3} ')

strPatterns = [
    strPattern0, strPattern1, strPattern2, strPattern3,
    strPattern4, strPattern5, strPattern6
]

"""
Patterns for specific lines which I want to remove
"""
sLinePattern0 = re.compile(r'\*')
sLinePattern1 = re.compile(r'\+{10}')
sLinePattern2 = re.compile(r'Received DBC-REQ \(trans. id\=')
sLinePattern3 = re.compile(r'RCC->')
sLinePattern4 = re.compile(r'TCC->')
sLinePattern5 = re.compile(r'\d')

sLinePatterns = [
    sLinePattern0,
    sLinePattern1,
    sLinePattern2,
    sLinePattern3,
    sLinePattern4,
    sLinePattern5
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
Patterns for specific lines which I want to make them as primary
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
Patterns for other specific lines
"""
# DS/US channel status tables
dsChStatTablePattern = re.compile(r'Active Downstream Channel Diagnostics\:')
usChStatTablePattern = re.compile(r'Active Upstream Channels\:')
# Common table
commonTablePattern = re.compile(r' *----')
# Initial ranging block for each UCID
initRangePattern = re.compile(r'== Beginning initial ranging for Docsis UCID')

"""
Variables initialization
"""
inDsChStatTable = False
inUsChStatTable = False
tableMessed = False
dsTableEntryProcessed = False
lastLineMessed = False
inTable = False
inMultiLineCnt = 0
lastLineEmpty = False
sccvEmptyLineCnt = 0

"""
1). Remove timestamps, console prompts, tables, empty lines
2). Make an nested line as primary if two more empty lines proceeded
3). Make some specific lines as primary
"""
for line in file:
    """
    Remove the unwanted strings which include some kind of timestamps, console prompts and etc.
    """
    """
    newline0 = pattern0.sub('', line)
    #print(newline0, '')
    newline1 = pattern1.sub('', newline0)
    newline2 = pattern2.sub('', newline1)
    newline3 = pattern3.sub('', newline2)
    newline4 = pattern4.sub('', newline3)
    """
    newline = line

    # Remove timestamp, console prompt and others
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
    #       0*    1   300000000   y    y          35            3      Qam256
    #       1     2   308000000   y    y          34            4      Qam256
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

            newline = 'DS channel status' + ', rxid ' + lineList[0] + ', dcid ' + lineList[1] + \
                      ', freq ' + lineList[2] + ', qam ' + lineList[3] + ', fec ' + lineList[4] + \
                      ', snr ' + lineList[5] + ', power ' + lineList[6] + ', mod ' + lineList[7]

    # Format US channel status table
    #
    # Active Upstream Channels:
    #
    #                     rng     pwr        frequency     symbols   phy  ok tx
    #  txid  ucid  dcid   sid     dBmv          MHz          sec    type  data?
    #  ----  ----  ----  ------  -----    ---------------  -------  ----  -----
    #     0   101     1     0x2      18             9.000  5120000     3      y
    #     1   102     1     0x2      18            15.400  5120000     3      y
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
            # US channel status, txid 0, ucid 101, dcid 1, rngsid 0x2, power 18, freq 9.000, symrate 5120000, phytype 3, txdata y
            lineList = newline.split(None, 8)
            if lineList[6] == '-':
                # This line is for OFDMA channel, so split it again
                lineList = newline.split(None, 10)
                newline = 'US channel status' + ', txid ' + lineList[0] + ', ucid ' + lineList[1] + \
                          ', dcid ' + lineList[2] + ', rngsid ' + lineList[3] + ', power ' + lineList[4] + \
                          ', freq ' + lineList[5] + ' ' +lineList[6] + ' ' + lineList[7] + \
                          ', symrate ' + lineList[8] + ', phytype ' + lineList[9] + \
                          ', txdata ' + lineList[10]
            else:
                # For SC-QAM channels
                newline = 'US channel status' + ', txid ' + lineList[0] + ', ucid ' + lineList[1] + \
                          ', dcid ' + lineList[2] + ', rngsid ' + lineList[3] + ', power ' + lineList[4] + \
                          ', freq ' + lineList[5] + ', symrate ' + lineList[6] + ', phytype ' + lineList[7] + \
                          ', txdata ' + lineList[8]

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
        inMultiLineCnt = 1
    elif inMultiLineCnt >= 1:
        if ((inMultiLineCnt > 8) or
            ((newline in ['\n', '\r\n']) and (inMultiLineCnt in [7, 8, 9])) or
            ((newline not in ['\n', '\r\n']) and (inMultiLineCnt == 7) and (not nestedLinePattern.match(newline)) and (not re.match(r'BcmCmUsChan', newline)))):
            # Suppose multi-line log ended with empty line or with special cases
            inMultiLineCnt = 0
        else:
            # Still multi-line, indent it, say add a space at the start
            inMultiLineCnt += 1
            newline = ' ' + newline

    # Indent some specific lines
    for pattern in sPrimaryLinePatterns:
        match = pattern.match(newline)
        if match:
            # Indent this line
            newline = ' ' + newline

    # It is time to remove empty line
    if newline in ['\n', '\r\n']:
        if lastLineEmpty == False:
            sccvEmptyLineCnt = 1
        else:
            sccvEmptyLineCnt += 1

        # Update lastLineEmpty for the next line processing
        lastLineEmpty = True
        continue

    # Make a nested line as primary if two more empty lines proceeded
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

    # Make some specific nested lines as primary
    for pattern in sNestedLinePatterns:
        match = pattern.match(newline)
        if match:
            newline = newline.lstrip()
            break

    # Update lastLineEmpty for the next line processing
    lastLineEmpty = False

    newfile.write(newline)

file.close()
newfile.close()

# Scan the new generated newfile
newfile    = open(parentdir + '/logs/test_new.txt', 'r')
normfile   = open(parentdir + '/logs/test_norm.txt', 'w')

"""
Variables initialization
"""
# The lastLine is initialized as empty w/o LF or CRLF
lastLine = ''

"""
Concatenate nested line to its parent (primary) line
"""
for line in newfile:

    if nestedLinePattern.match(line):
        # Concatenate current line to lastLine
        lastLine = lastLine.rstrip()
        lastLine += ', '
        lastLine += line.lstrip()
    else:
        # If current is primary line, it means concatenation ends
        normfile.write(lastLine)
        lastLine = line

newfile.close()
normfile.close()