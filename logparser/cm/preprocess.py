#!/usr/bin/env python3
"""
Description : This file cleans / formats the raw CM/DOCSIS logs
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import re
import sys
import pickle
from datetime import datetime
from tqdm import tqdm

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
grandpadir = os.path.abspath(os.path.join(parentdir, os.path.pardir))
#sys.path.append(grandpadir)

#from tools import helper

#----------------------------------------------------------------------------------------
# Process the train data or test data. Read also other info from config file.
#----------------------------------------------------------------------------------------
#
with open(grandpadir+'/entrance/config.txt', 'r', encoding='utf-8-sig') as confile:
    conlines = confile.readlines()

    TRAINING = bool(conlines[1].strip() == 'TRAINING=1')
    METRICSEN = bool(conlines[2].strip() == 'METRICS=1')
    DLOGCONTEXT = bool(conlines[3].strip() == 'MODEL=DEEPLOG')
    OSSCONTEXT = bool(conlines[3].strip() == 'MODEL=OSS')
    LLABCONTEXT = bool(conlines[3].strip()[0:12] == 'MODEL=LOGLAB')

if TRAINING:
    raw_file_loc = grandpadir + '/logs/cm/train.txt'
    new_file_loc = grandpadir + '/logs/cm/train_new.txt'
    norm_file_loc = grandpadir + '/logs/cm/train_norm.txt'
    DATATYPE = 'train'
else:
    raw_file_loc = grandpadir + '/logs/cm/test.txt'
    new_file_loc = grandpadir + '/logs/cm/test_new.txt'
    norm_file_loc = grandpadir + '/logs/cm/test_norm.txt'
    runtime_para_loc = grandpadir + '/results/test/cm/test_runtime_para.txt'
    rawln_idx_loc = grandpadir + '/results/test/cm/rawline_idx_norm.pkl'
    rawLnIdxVectorNew = []
    rawLnIdxVectorNorm = []
    DATATYPE = 'test'

# The main timestamp flag. The default offset value comes from strPattern0 below.
RESERVE_TS = True
LOG_HEAD_OFFSET = 24

# ---------------------------------------------------
# RESERVE_TS == -1: Not valid log file for LOG_TYPE
# RESERVE_TS ==  0: Valid log file without timestamp
# RESERVE_TS >   0: Valid log file with timestamp
# ---------------------------------------------------
if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)):
    with open(runtime_para_loc, 'r') as parafile:
        paralines = parafile.readlines()
        LOG_HEAD_OFFSET = int(paralines[0].strip().replace('RESERVE_TS=', ''))

    if LOG_HEAD_OFFSET > 0:
        RESERVE_TS = True
    elif LOG_HEAD_OFFSET == 0:
        RESERVE_TS = False
    else:
        # Not a LOG_TYPE log file
        sys.exit(0)

#
# The original log usually comes from serial console tools like SecureCRT
# in Windows and the text file encoding is probably utf-8 (with BOM).
# https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8
#
# To let python skip the BOM when decoding the file, use utf-8-sig codec.
# https://docs.python.org/3/library/codecs.html
#
rawfile = open(raw_file_loc, 'r', encoding='utf-8-sig')
newfile = open(new_file_loc, 'w', encoding='utf-8')

#---------------------------------------------
# Definitions:
# primary line - no space proceeded
# nested line  - one or more spaces proceeded
# empty line   - LF or CRLF only in one line
#---------------------------------------------

#----------------------------------------------------------------------------------------
# Patterns for removing timestamp, console prompt and others
#----------------------------------------------------------------------------------------
# The pattern for the timestamp added by console tool, e.g. [20190719-08:58:23.738].
# Loglizer Label, Deeplog segment sign and Loglab class label are also considered.
if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)):
    strPattern0 = re.compile(r'.{%d}' % LOG_HEAD_OFFSET)
else:
    strPattern0 = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
                             r'\.(\d{3})|24:00:00\.000)\] (abn: )?(segsign: )?(c[0-9]{3} )?')

# The pattern for CM console prompts
strPattern1 = re.compile('CM[/a-z-_ ]*> ', re.IGNORECASE)
# The pattern for the timestamp added by BFC, e.g. [00:00:35 01/01/1970], [11/21/2018 14:49:32]
# or emta specific "00:00:35.012 01/01/1970  "
strPattern2 = re.compile(r'\[?(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)(.\d\d\d)?|24:00:00(.000)?) '
                         r'\d{2}/\d{2}/\d{4}\]?  ?')
strPattern3 = re.compile(r'\[\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)\] ')
# The pattern for the timestamp added by others, e.g. 01/01/1970 00:00:19
strPattern4 = re.compile(r'\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) - ')
# The pattern for the tag of thread
strPattern5 = re.compile(r'\[ ?[a-z][a-z0-9\- ]*\] ', re.IGNORECASE)
strPattern6 = re.compile(r'\+{3} ')
# The pattern for the instance name of BFC class
strPattern7 = re.compile(r'(?<=:  )\([a-zA-Z0-9/ ]+\) ')

strPatterns = [
    strPattern1, strPattern2, strPattern3, strPattern4,
    strPattern5, strPattern6, strPattern7,
]

#----------------------------------------------------------------------------------------
# Patterns for fuzzy time format, e.g. 12:34:56, 12-34-56, 12/34/56, etc.
#----------------------------------------------------------------------------------------
fuzzyTimePattern = re.compile(r'[0-5][0-9][^a-zA-Z0-9 ][0-5][0-9][^a-zA-Z0-9 ][0-5][0-9]')

#----------------------------------------------------------------------------------------
# Patterns for specific lines which I want to remove
#----------------------------------------------------------------------------------------
sLinePattern0 = re.compile(r'\*|BCM3390\d+|RAM Windows size \d+ mb')
sLinePattern1 = re.compile(r'\+{10}|\+-{5}')
sLinePattern2 = re.compile(r'BCM339[0-9]+[a-zA-Z]*[0-9] Bootloader version')
sLinePattern3 = re.compile(r'RCC->')
sLinePattern4 = re.compile(r'TCC->')
sLinePattern5 = re.compile(r'\d+\*')
sLinePattern6 = re.compile(r'Readback Test pkt\:')
sLinePattern7 = re.compile(r'DHCPc\:  Timed out waiting for offers for lease')
sLinePattern8 = re.compile(r'fUsSetsState = ')
sLinePattern9 = re.compile(r'( {7}munged error type: T=)|'
                           r'( {5}munged error type =)|'
                           r'( {5}partial svc dcid\(s\): T=)')
sLinePattern10 = re.compile(r'Type \'help\' or')
sLinePattern11 = re.compile(r' {24}dsid: | {24}DSID: | {24}CMIM: ')
sLinePattern12 = re.compile(r'={18}')
sLinePattern13 = re.compile(r'Suboption \d:|'
                            r'eptAsyncCmd: Ept not initialized|'
                            r'\([a-zA-Z0-9]+\)|'
                            r'Len: \d+ ')

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
    sLinePattern9,
    sLinePattern10,
    sLinePattern11,
    sLinePattern12,
    sLinePattern13,
]

#----------------------------------------------------------------------------------------
# Patterns for removing Table headers
#----------------------------------------------------------------------------------------
title00 = re.compile(r' *Trimmed Candidate Downstream Service Group')
title01 = re.compile(r' *sgid +size +member')
title02 = re.compile(r' *Downstream Active Channel Settings')
title03 = re.compile(r' *dcid +type +frequency')
title04 = re.compile(r' *Upstream Active Channel Settings')
title05 = re.compile(r' *ucid +rpt enable')
title06 = re.compile(r' *BcmCmUsTargetMset \(a.k.a. usable UCDs')
title07 = re.compile(r' *us +config')
title08 = re.compile(r' *phy +change')
title09 = re.compile(r' *type +ucid +dcid +count')
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
title23 = re.compile(r' {5}US chan ID {5}Tx Power \(dBmV\)')

titlePatterns = [
    title00, title01, title02, title03, title04, title05, title06, title07,
    title08, title09, title10, title11, title12, title13, title14, title15,
    title16, title17, title18, title19, title20, title21, title22, title23,
]

#----------------------------------------------------------------------------------------
# Patterns for hex blocks in MMM pdu, which I want to remove
#----------------------------------------------------------------------------------------
pduHexBlkHeaderPattern0 = re.compile(r' {13}description: T=')
pduHexBlkHeaderPattern1 = re.compile(r' {11}description =')
pduHexBlkBodyPattern = re.compile(r' {2}[a-f0-9]{2} ')

pduHexBlkHeaderPatterns = [
    pduHexBlkHeaderPattern0,
    pduHexBlkHeaderPattern1,
]

#----------------------------------------------------------------------------------------
# Pattern for nested line
#----------------------------------------------------------------------------------------
nestedLinePattern = re.compile(r' +|\t+')

#----------------------------------------------------------------------------------------
# Patterns for specific primary lines which I want to indent them
#----------------------------------------------------------------------------------------
sPrimaryLinePattern0 = re.compile(r'Assigned OFDMA Data Profile IUCs')
sPrimaryLinePattern1 = re.compile(r'fDestSingleTxTargetUsChanId')
sPrimaryLinePattern2 = re.compile(r'fTmT4NoUnicastRngOpStdMlsec')
sPrimaryLinePattern3 = re.compile(r'MSG PDU:')
sPrimaryLinePattern4 = re.compile(r'to a CM prior to sending')
sPrimaryLinePattern5 = re.compile(r'Load Address: ')

sPrimaryLinePatterns = [
    sPrimaryLinePattern0,
    sPrimaryLinePattern1,
    sPrimaryLinePattern2,
    sPrimaryLinePattern3,
    sPrimaryLinePattern4,
    sPrimaryLinePattern5,
]

#----------------------------------------------------------------------------------------
# Patterns for a block/table of lines which I want to indent them
# Empty line indicates the end of the block
# Run this before removing empty lines
#----------------------------------------------------------------------------------------
blockTitlePattern0 = re.compile(r'===== Read Leap AIF Status =====')

blockTitlePatterns = [
    blockTitlePattern0
]

#----------------------------------------------------------------------------------------
# Patterns for specific lines which I want to convert them as primary
#----------------------------------------------------------------------------------------
sNestedLinePattern0 = re.compile(r' +DOWNSTREAM STATUS')
sNestedLinePattern1 = re.compile(r' +CM Upstream channel info')
sNestedLinePattern2 = re.compile(r' +Receive Channel Config\:')
sNestedLinePattern3 = re.compile(r' Reason = ')
sNestedLinePattern4 = re.compile(r'\t{7}Storing to device...|'
                                 r'\t{7}Loading from server...|'
                                 r'  CmSnmpAgent::|'
                                 r'  DefaultSnmpAgentClass::|'
                                 r'  Special case: don\'t disable|'
                                 r'  [DU]S: +\d+ SC-QAM \(0x')
sNestedLinePattern5 = re.compile(r'  Plant power is')

sNestedLinePatterns = [
    sNestedLinePattern0,
    sNestedLinePattern1,
    sNestedLinePattern2,
    sNestedLinePattern3,
    sNestedLinePattern4,
    sNestedLinePattern5,
]

#----------------------------------------------------------------------------------------
# Patterns for nested lines (exceptions) which I do not want to make them as primary
#----------------------------------------------------------------------------------------
eNestedLinePattern0 = re.compile(r' +Ranging state info:')

eNestedLinePatterns = [
    eNestedLinePattern0
]

#----------------------------------------------------------------------------------------
# Patterns for specific whole multi-line log which I want to remove entirely
# Block end condition: primary line (exclusive)
#----------------------------------------------------------------------------------------
wMultiLineRmPattern0 = re.compile(r'Configured O-INIT-RNG-REQ :')
wMultiLineRmPattern1 = re.compile(r' {4}tap values:')
wMultiLineRmPattern2 = re.compile(r' *Trimmed Downstream Ambiguity Resolution Frequency List')

wMultiLineRmPatterns = [
    wMultiLineRmPattern0,
    wMultiLineRmPattern1,
    wMultiLineRmPattern2,
]

#----------------------------------------------------------------------------------------
# Patterns for block of logs which I want to remove entirely
# [logBlockStart: inclusive, logBlockEnd: exclusive)
#----------------------------------------------------------------------------------------
logBlockSrt0 = re.compile(r'\| This image is built using remote flash as nonvol.')
logBlockEnd0 = re.compile(r'>>>>ChipID=0x339\d+')
logBlockSrt1 = re.compile(r'Downloading LEAP image')
logBlockEnd1 = re.compile(r'>>>AP dload time')
logBlockSrt2 = re.compile(r'Initializing DS Docsis 3.0 MAC')
logBlockEnd2 = re.compile(r'(Running the system...)|(Automatically stopping at console)')

logBlockPatterns = [
    [logBlockSrt0, logBlockEnd0],
    [logBlockSrt1, logBlockEnd1],
    [logBlockSrt2, logBlockEnd2],
]

#----------------------------------------------------------------------------------------
# Patterns for other specific lines
#----------------------------------------------------------------------------------------
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
# Split assignment token something like ABC=xyz or ABC==xyz
assignTokenPattern = re.compile(r'=(?=[^= \r\n])')
# Split cpp class token like ABC::Xyz or ABC::xY
cppClassPattern = re.compile(r'\:\:(?=[A-Z][a-z0-9]|[a-z][A-Z])')
# Split 'ABC;DEF' to 'ABC; DEF'
semicolonPattern = re.compile(r';(?! )')
# Split hash number like #123 to # 123
hashNumPattern = re.compile(r'#(?=[0-9]+)')
# Change something like (xx), [xx], ..., to ( xx ), [ xx ], ...
bracketPattern1 = re.compile(r'\((?=(\w|[-+]))')
bracketPattern2 = re.compile(r'(?<=\w)\)')
bracketPattern3 = re.compile(r'\[(?=(\w|[-+]))')
bracketPattern4 = re.compile(r'(?<=\w)\]')
bracketPattern5 = re.compile(r'\d+(?=(ms))')
#bracketPattern6 = re.compile(r'(?<=\.\.)\d')

#----------------------------------------------------------------------------------------
# Patterns for logs that I want to add the session label 'segsign: '
#----------------------------------------------------------------------------------------
sessionPattern0 = re.compile(r'Loading compressed image \d')
sessionPattern1 = re.compile(r'Moving to Downstream Frequency')

sessionPatterns = [
    sessionPattern0,
    sessionPattern1,
]

#----------------------------------------------------------------------------------------
# Patterns for segment labels, 'segsign: ' or 'cxxx '
#----------------------------------------------------------------------------------------
label_pattern = re.compile(r'(segsign: )|(c[0-9]{3} )')


#########################################################################################
# 1. Start data cleaning and formating
#########################################################################################

#-------------------------
# Variables initialization
#-------------------------
heading_clean = False
inDsChStatTable = False
inUsChStatTable = False
tableMessed = False
dsTableEntryProcessed = False
lastLineMessed = False
inTable = False
inHexBlock = False
inLogBlock = False
inMultiLineInitRange = False
inMultiLineRemove = False
inLogBlockPrim = False
lastLineEmpty = False
sccvEmptyLineCnt = 0
lastLabelRemoved = False
lastLabel = ''

#----------------------------------------------------------------------
# 01) Extrace timestamps, remove console prompts, etc.
# 02) Remove log blocks
# 03) Format DS/US channel status tables
# 04) Remove some tables which are useless
# 05) Remove hex blocks in mmm pdu
# 06) Format initial ranging block to one line log
# 07) Indent some specific lines in multi-line log
# 08) Indent a block of lines, note: run it before removing empty lines
# 09) Remove empty lines
# 10) Convert nested line as primary if two more empty lines proceeded
# 11) Convert some specific lines as primary
# 12) Remove specific whole multi-line log
# 13) Split some tokens
# 14) Add segmentation sign for DeepLog train dataset
#----------------------------------------------------------------------
print("Pre-processing the raw {0} dataset ...".format(DATATYPE))
parse_st = datetime.now()
linesLst = rawfile.readlines()
rawsize = len(linesLst)

# Decide if we reserve the main timestamp by checking the first line of the log file
# So we always suppose the first line of the log file is good and not messed up.
# Only do for deeplog/loglab predict (including oss). The loglizer predict must have
# standard timestamp.

#--block comment out start--
#if (not TRAINING) and (not METRICSEN):
#    for line in linesLst:
#        # Skip the heading empty lines if any exist
#        if line in ['\n', '\r\n']:
#            continue
#        RESERVE_TS = strPattern0.match(line)
#        break
#--end--

#
# A low overhead progress bar
# https://github.com/tqdm/tqdm#documentation
# If only display statics w/o bar, set ncols=0
#
pbar = tqdm(total=rawsize, unit='Lines', disable=False,
            bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

for _idx, line in enumerate(linesLst):
#for line in rawfile:

    # Update the progress bar
    #helper.printProgressBar(_idx+1, rawsize, prefix='Progress:')
    pbar.update(1)

    #------------------------------------------------------------------------------------
    # Remove unwanted strings including some kind of timestamps, console prompts and etc.
    #------------------------------------------------------------------------------------
    # Save the main timestamp if it exists. The newline does not have the main timestamp
    # before write it back to a new file. The train label and the session label are also
    # considered. Add them back along with the main timestamp at the end.
    matchTS = strPattern0.match(line)
    if RESERVE_TS and matchTS:
        # Strip off the main timestamp including train and session labels if any exist
        currentLineTS = matchTS.group(0)
        if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)) \
            and (not fuzzyTimePattern.search(currentLineTS)):
            if _idx == 0:
                heading_clean = True
            continue
        newline = strPattern0.sub('', line, count=1)
        # Inherit segment labels (segsign: or cxxx) from last labeled line if it is removed
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN) and lastLabelRemoved:
            currentLineTS += lastLabel
            # Reset
            lastLabelRemoved = False
            lastLabel = ''
    elif RESERVE_TS:
        # If we intend to reserve the main timestamp but does not match, delete this line
        # This usually happens when the timestamp is messed up, the timestamp format is
        # not recognized, or no timestamp at all at the head of some log.
        if _idx == 0:
            heading_clean = True
        continue
    else:
        # No main timestamp in the log file or we do not want to reserve it
        newline = line

    # Remove some heading lines at the start of log file
    if (_idx == 0 or heading_clean) \
        and (nestedLinePattern.match(newline) or newline in ['\n', '\r\n']):
        heading_clean = True
        # Take care if the removed line has segment label. Hand it to the next line
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN):
            label_match = label_pattern.search(currentLineTS)
            if label_match:
                lastLabel = label_match.group(0)
                lastLabelRemoved = True
        continue
    if heading_clean:
        heading_clean = False

    #------------------------------------------------------------------------------------
    # No main timestamp and train label at start of each line in the remaining of the loop
    #------------------------------------------------------------------------------------
    # Remove remaining timestamps, console prompts and others
    for pattern in strPatterns:
        newline = pattern.sub('', newline, count=1)

    # Remove the line if the timestamp appears in the middle because of code bug w/o endl.
    if strPattern2.search(newline):
        # Update for the next line
        lastLineEmpty = False
        continue

    # Remove some log blocks
    foundStart = False
    foundEnd = False
    for patternStart, patternEnd in logBlockPatterns:
        if patternStart.match(newline):
            foundStart = True
            break
        if patternEnd.match(newline):
            foundEnd = True
            break
    if foundStart:
        inLogBlock = True
        # Delete current line
        # Update for the next line
        lastLineEmpty = False
        continue
    if inLogBlock:
        if foundEnd:
            inLogBlock = False
        else:
            # Delete current line
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
    if goNextLine:
        # Take care if the removed line has segment label. Hand it to the next line
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN):
            label_match = label_pattern.search(currentLineTS)
            if label_match:
                lastLabel = label_match.group(0)
                lastLabelRemoved = True
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
    if inTable:
        if newline in ['\n', '\r\n']:
            # Suppose table ended with empty line
            # Note: we also reset the inTable for the DS/US channel status table above
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
    if goNextLine:
        # Update for the next line
        lastLineEmpty = False
        continue

    # Remove hex blocks in the MMM pdu
    goNextLine = False
    for pattern in pduHexBlkHeaderPatterns:
        match = pattern.match(newline)
        if match:
            goNextLine = True
            break
    if goNextLine:
        inHexBlock = True
        # Update for the next line
        lastLineEmpty = False
        continue
    if inHexBlock:
        match = pduHexBlkBodyPattern.match(newline)
        if match:
            # Update for the next line
            lastLineEmpty = False
            continue
        inHexBlock = False

    # Indent lines as multi-line log for initial ranging
    # Note: the block ending is special
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

    # Indent a block of lines from primary to embedded
    # Note: the block ending is an empty line
    foundPattern = False
    for pattern in blockTitlePatterns:
        if pattern.match(newline):
            foundPattern = True
            break
    if foundPattern:
        inLogBlockPrim = True
        # Keep the title line and goto next line now
    elif inLogBlockPrim:
        # Indent the line if it is not empty
        if newline in ['\n', '\r\n']:
            inLogBlockPrim = False
        else:
            newline = ' ' + newline

    # It is time to remove empty line
    if newline in ['\n', '\r\n']:
        if lastLineEmpty == False:
            sccvEmptyLineCnt = 1
        else:
            sccvEmptyLineCnt += 1

        # Take care if the removed line has segment label. Hand it to the next line
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN):
            label_match = label_pattern.search(currentLineTS)
            if label_match:
                lastLabel = label_match.group(0)
                lastLabelRemoved = True

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
    if inMultiLineRemove:
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

    # Split hash number like #123 to # 123
    newline = hashNumPattern.sub('# ', newline)

    # Change something like (xx), [xx], ..., to ( xx ), [ xx ], ...
    newline = bracketPattern1.sub('( ', newline)
    newline = bracketPattern2.sub(' )', newline)
    newline = bracketPattern3.sub('[ ', newline)
    newline = bracketPattern4.sub(' ]', newline)

    m = bracketPattern5.search(newline)
    if m:
        substring = m.group(0)
        newline = bracketPattern5.sub(substring+' ', newline)

    #--block comment out start--
    #m = bracketPattern6.search(newline)
    #if m:
    #    substring = m.group(0)
    #    newline = bracketPattern6.sub(' '+substring, newline)
    #--end--

    #--------------------------------------------------------------
    # Add session label 'segsign: ' for DeepLog
    # In DeepLog train or validation, we use the multi-session logs
    # METRICSEN means we do validation on the test dataset or not
    #--------------------------------------------------------------
    if DLOGCONTEXT and (TRAINING or METRICSEN):
        for pattern in sessionPatterns:
            if pattern.match(newline):
                newline = 'segsign: ' + newline

    # Update lastLineEmpty for the next line processing
    lastLineEmpty = False

    # Write current line to a new file with the timestamp if it exists
    if RESERVE_TS and matchTS:
        newline = currentLineTS + newline
    newfile.write(newline)

    # The raw line index list in the new file
    # Do it only for prediction in DeepLog/Loglab and OSS
    if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)):
        rawLnIdxVectorNew.append(_idx+1)

pbar.close()
rawfile.close()
newfile.close()
print('Purge costs {!s}\n'.format(datetime.now()-parse_st))


#########################################################################################
# 2. Convert multi-line log to one-line format
#    Calculate the raw line idx for test dataset
#########################################################################################

# Scan the new generated newfile
newfile = open(new_file_loc, 'r', encoding='utf-8')
normfile = open(norm_file_loc, 'w', encoding='utf-8')

#
# Variables initialization
#
# The lastLine is initialized as empty w/o LF or CRLF
lastLine = ''
lastLineTS = ''

#
# Concatenate nested line to its parent (primary) line
#
for _idx, line in enumerate(newfile):
    # Save timestamp if it exists. Only two cases: match or no main timestamp
    matchTS = strPattern0.match(line)
    if RESERVE_TS and matchTS:
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
        if RESERVE_TS and matchTS and (lastLine != ''):
            lastLine = lastLineTS + lastLine
        normfile.write(lastLine)

        # The raw line index list based on the norm file
        # Mapping: norm file line index (0-based) -> test file line index (1-based)
        # Do it only for prediction in DeepLog/Loglab and OSS
        if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)):
            rawLnIdxVectorNorm.append(rawLnIdxVectorNew[_idx])

        # Update last line parameters
        lastLine = newline
        if RESERVE_TS and matchTS:
            lastLineTS = currentLineTS

# Write the last line of the file
if RESERVE_TS and matchTS and (lastLine != ''):
    lastLine = lastLineTS + lastLine
normfile.write(lastLine)

newfile.close()
normfile.close()

# Write the raw line index list based on norm file to disk
# Write the RESERVE_TS value to the realtime parameter file
# Do it only for prediction in DeepLog/Loglab and OSS
if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)):
    with open(rawln_idx_loc, 'wb') as f:
        pickle.dump(rawLnIdxVectorNorm, f)

    #with open(runtime_para_loc, 'w') as f:
    #    f.write('RESERVE_TS=1' if RESERVE_TS else 'RESERVE_TS=0')
