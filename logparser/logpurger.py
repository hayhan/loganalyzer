#!/usr/bin/env python3
import os
import re

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
file       = open(parentdir + '/logs/test.txt', 'r')
newfile    = open(parentdir + '/logs/test_new.txt', 'w')

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

inTable = False
lastLineEmpty = False
sccvEmptyLineCnt = 0
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

    # Remove specific table titles
    match = re.match(r' *Trimmed Candidate Downstream Service Group Settings List', newline)
    if match:
        continue

    match = re.match(r' *sgid  size  member', newline)
    if match:
        continue

    match = re.match(r' *Downstream Active Channel Settings', newline)
    if match:
        continue

    match = re.match(r' *dcid      type  frequency', newline)
    if match:
        continue

    match = re.match(r' *Upstream Active Channel Settings', newline)
    if match:
        continue

    match = re.match(r' *ucid  rpt enable', newline)
    if match:
        continue

    match = re.match(r'BcmCmUsTargetMset (a.k.a. usable UCDs gathered during startup):', newline)
    if match:
        continue

    match = re.match(r'   us               config', newline)
    if match:
        continue

    match = re.match(r'   phy              change', newline)
    if match:
        continue

    match = re.match(r'  type  ucid  dcid  count', newline)
    if match:
        continue

    match = re.match(r'REG-RSP-MP Summary:', newline)
    if match:
        continue

    match = re.match(r'TCC commands->', newline)
    if match:
        continue

    match = re.match(r'ucid      action             ranging strategy', newline)
    if match:
        continue

    match = re.match(r'Service Flow settings->', newline)
    if match:
        continue

    match = re.match(r'sfid         sid              ucids', newline)
    if match:
        continue

    match = re.match(r'DSID settings->', newline)
    if match:
        continue

    match = re.match(r'dsid         action    reseq', newline)
    if match:
        continue

    match = re.match(r'Active Downstream Channel Diagnostics:', newline)
    if match:
        continue

    match = re.match(r'  rx id  dcid    freq', newline)
    if match:
        continue

    match = re.match(r'                           plc  prfA', newline)
    if match:
        continue

    match = re.match(r'Active Upstream Channels:', newline)
    if match:
        continue

    match = re.match(r'                    rng     pwr', newline)
    if match:
        continue

    match = re.match(r' txid  ucid  dcid   sid', newline)
    if match:
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

    else:
        # Update lastLineEmpty for the next line processing
        lastLineEmpty = False

    # Process nested line now

    newfile.write(newline)

file.close()
newfile.close()