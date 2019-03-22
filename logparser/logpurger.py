#!/usr/bin/env python3
import os
import re

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
file       = open(parentdir + '/logs/test.txt', 'r')
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
pattern0 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d):(\d{3})|24:00:00:000)\]')
# The pattern for CM console prompts
pattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
# The pattern for the timestamp added by BFC
pattern2 = re.compile(r'\[(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{2}/\d{2}/\d{4}\] ')
pattern3 = re.compile(r'\[\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)\] ')
# The pattern for the timestamp added by others
pattern4 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')
# The pattern for the tag of thread
pattern5 = re.compile(r'\[[a-z ]*\] ', re.IGNORECASE)

regexPatterns = [pattern0, pattern1, pattern2, pattern3, pattern4, pattern5]

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
Patterns for specific lines which I want to make them as primary
"""
nestedLinePatternSpec0 = re.compile(r' +DOWNSTREAM STATUS')

nestedLinePatternSpec = [
    nestedLinePatternSpec0
]

"""
Variables initialization
"""
inTable = False
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
    for pattern in regexPatterns:
        newline = pattern.sub('', newline, count=1)

    # Remove line starting with '*'
    match = re.match(r'\*', newline)
    if match:
        continue

    # Remove table starting with "----", " ----" or "  ----"
    match = re.match(r' *----', newline)
    if match:
        inTable = True
        continue
    elif inTable == True:
        if newline in ['\n', '\r\n']:
            # Suppose table ended with empty line
            inTable = False
        else:
            # Still table line, remove it
            continue

    # Remove specific table title line
    goNextLine = False
    for pattern in titlePatterns:
        match = pattern.match(newline)
        if match:
            goNextLine = True
            break
    if goNextLine == True:
        continue

    # It is time to remove empty line
    if newline in ['\n', '\r\n']:
        if lastLineEmpty == False:
            sccvEmptyLineCnt = 1
        else:
            sccvEmptyLineCnt += 1

        # Update lastLineEmpty for the next line processing
        lastLineEmpty = True
        continue

    # Make an nested line as primary if two more empty lines proceeded
    if nestedLinePattern.match(newline):
        if (lastLineEmpty == True) and (sccvEmptyLineCnt >= 2):
            newline = newline.lstrip()

    # Make some specific lines as primary
    for pattern in nestedLinePatternSpec:
        match = pattern.match(newline)
        if match:
            newline = newline.lstrip()

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
        lastLine += ' '
        lastLine += line.lstrip()
    else:
        # If current is primary line, it means concatenation ends
        normfile.write(lastLine)
        lastLine = line

newfile.close()
normfile.close()