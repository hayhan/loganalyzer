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

# The main timestamp flag. The default offset value comes from PTN_MAIN_TS below.
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
    PTN_MAIN_TS = re.compile(r'.{%d}' % LOG_HEAD_OFFSET)
else:
    PTN_MAIN_TS = re.compile(r'\[\d{4}\d{2}\d{2}-(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)'
                             r'\.(\d{3})|24:00:00\.000)\] (abn: )?(segsign: )?(c[0-9]{3} )?')

PTN_BFC_TS = re.compile(
    # BFC timestamps [00:00:35 01/01/1970]
    r'\[?(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00(.000)?) \d{2}/\d{2}/\d{4}\]?  ?'
)

PTN_CLEAN_CHAR = re.compile(
    # CM console prompts
    r'CM[/a-z-_ ]*> |'
    # BFC timestamps [00:00:35 01/01/1970], "00:00:35.012 01/01/1970  "
    r'\[?(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)(.\d\d\d)?|24:00:00(.000)?) \d{2}/\d{2}/\d{4}\]?  ?|'
    # BFC timestamps [11/21/2018 14:49:32]
    r'\[\d{2}/\d{2}/\d{4} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)\] (- )?|'
    # Tag of thread
    r'\[ ?[a-z][a-z0-9\- ]*\] |'
    # Instance name of BFC class
    r'(?<=:  )\([a-zA-Z0-9/ ]+\) |'
    # Misc unwanted chars embedded in the log
    r'\+{3} ',

    re.IGNORECASE
)


#----------------------------------------------------------------------------------------
# Patterns for fuzzy time format, e.g. 12:34:56, 12-34-56, 12/34/56, etc.
#----------------------------------------------------------------------------------------
PTN_FUZZY_TIME = re.compile(
    r'[0-5][0-9][^a-zA-Z0-9 ][0-5][0-9][^a-zA-Z0-9 ][0-5][0-9]'
)

#----------------------------------------------------------------------------------------
# Pattern for removing specific lines
#----------------------------------------------------------------------------------------
PTN_LINE_RM = re.compile(
    r'\*|BCM3390\d+|RAM Windows size \d+ mb|'
    r'\+{10}|\+-{5}|'
    r'BCM339[0-9]+[a-zA-Z]*[0-9] Bootloader version|'
    r'RCC->|'
    r'TCC->|'
    r'\d+\*|'
    r'Readback Test pkt\:|'
    r'DHCPc\:  Timed out waiting for offers for lease|'
    r'fUsSetsState = |'
    r'( {7}munged error type: T=)|'
    r'( {5}munged error type =)|'
    r'( {5}partial svc dcid\(s\): T=)|'
    r'Type \'help\' or|'
    r' {24}dsid: | {24}DSID: | {24}CMIM: |'
    r'={18}|'
    r'Suboption \d:|'
    r'eptAsyncCmd: Ept not initialized|'
    r'\([a-zA-Z0-9]+\)|'
    r'Len: \d+ |'
    # Hex line like "  00 10 18 de   f1 b8 c5 2e   14 56  | .........V"
    r'( {2}([0-9a-f]{2} ){1,4}){1,4} {1,52}\| '
)

#----------------------------------------------------------------------------------------
# Pattern for removing Table headers
#----------------------------------------------------------------------------------------
PTN_TABLE_TITLE = re.compile(
    r' *Trimmed Candidate Downstream Service Group|'
    r' *sgid +size +member|'
    r' *Downstream Active Channel Settings|'
    r' *dcid +type +frequency|'
    r' *Upstream Active Channel Settings|'
    r' *ucid +rpt enable|'
    r' *BcmCmUsTargetMset \(a.k.a. usable UCDs|'
    r' *us +config|'
    r' *phy +change|'
    r' *type +ucid +dcid +count|'
    r' *REG-RSP-MP Summary:|'
    r' *TCC commands->|'
    r' *ucid +action +ranging strategy|'
    r' *Service Flow settings->|'
    r' *sfid +sid +ucids|'
    r' *DSID settings->|'
    r' *dsid +action +reseq|'
    r' *Active Downstream Channel Diagnostics|'
    r' *rx id +dcid +freq|'
    r' *plc +prfA|'
    r' *Active Upstream Channels:|'
    r' *rng +pwr|'
    r' *txid +ucid +dcid +sid|'
    r' {5}US chan ID {5}Tx Power \(dBmV\)'
)

#----------------------------------------------------------------------------------------
# Pattern for nested line
#----------------------------------------------------------------------------------------
PTN_NESTED_LINE = re.compile(
    r' +|\t+'
)

#----------------------------------------------------------------------------------------
# Pattern for nested line (exceptions)
#----------------------------------------------------------------------------------------
PTN_NESTED_LINE_EXCEPTION = re.compile(
    r' +Ranging state info:'
)

#----------------------------------------------------------------------------------------
# Pattern for indenting specific primary lines
#----------------------------------------------------------------------------------------
PTN_PRI_TO_NESTED = re.compile(
    r'Assigned OFDMA Data Profile IUCs|'
    r'fDestSingleTxTargetUsChanId|'
    r'fTmT4NoUnicastRngOpStdMlsec|'
    r'MSG PDU:|'
    r'to a CM prior to sending|'
    r'Load Address: '
)

#----------------------------------------------------------------------------------------
# Pattern for indenting a block/table of lines
# Run this before removing empty lines
#----------------------------------------------------------------------------------------

# Do not indent the first line. Empty line indicates the block end
PTN_BLOCK_INDENT = re.compile(
    r'===== Read Leap AIF Status ====='
)

# Do not indent the first line. Special line indicates the block end
PTN_BLOCK_INDENT2 = re.compile(
    r'== Beginning initial ranging for Docsis UCID'
)

PTN_BLOCK_INDENT2_END = re.compile(
    r'Using clamped minimum transmit power|'
    r'Using bottom of DRW initial upstream power|'
    r'Using per transmitter stored initial upstream power'
)

#----------------------------------------------------------------------------------------
# Pattern for converting specific lines as primary
#----------------------------------------------------------------------------------------
PTN_NESTED_TO_PRI = re.compile(
    r' +DOWNSTREAM STATUS|'
    r' +CM Upstream channel info|'
    r' +Receive Channel Config\:|'
    r' Reason = |'
    r'\t{7}Storing to device...|'
    r'\t{7}Loading from server...|'
    r'  CmSnmpAgent::|'
    r'  DefaultSnmpAgentClass::|'
    r'  Special case: don\'t disable|'
    r'  [DU]S: +\d+ SC-QAM \(0x|'
    r'  Plant power is'
)

#----------------------------------------------------------------------------------------
# Pattern for whole multi-line log which should be removed entirely
# Block end condition: primary line (exclusive)
#----------------------------------------------------------------------------------------
PTN_BLOCK_RM_PRI = re.compile(
    r' {4}tap values:|'
    r' *Trimmed Downstream Ambiguity Resolution Frequency List'
)

#----------------------------------------------------------------------------------------
# Pattern for block of logs that should be removed entirely
# [BlockStart: inclusive, BlockEnd: exclusive)
#----------------------------------------------------------------------------------------
PTN_BLOCK_RM_START = re.compile(
    r'\| This image is built using remote flash as nonvol.|'
    r'Downloading LEAP image|'
    r'Initializing DS Docsis 3.0 MAC'
)

PTN_BLOCK_RM_END = re.compile(
    r'>>>>ChipID=0x339\d+|'
    r'>>>AP dload time|'
    r'(Running the system...)|(Automatically stopping at console)'
)

#----------------------------------------------------------------------------------------
# Pattern for other specific Tables
#----------------------------------------------------------------------------------------
# Common table
PTN_TABLE_TITLE_COMMON = re.compile(r' *----')
# DS/US channel status tables
dsChStatTablePattern = re.compile(r'Active Downstream Channel Diagnostics\:')
usChStatTablePattern = re.compile(r'Active Upstream Channels\:')


#----------------------------------------------------------------------------------------
# Pattern for spliting tokens
#----------------------------------------------------------------------------------------
PTN_SPLIT_LEFT = []
PTN_SPLIT_RIGHT = []

PTN_SPLIT_LEFT.append(
    # Split assignment token like ABC=xyz to ABC= xyz
    re.compile(r'=(?=[^= \r\n])')
)
PTN_SPLIT_LEFT.append(
    # Split cpp class token like ABC::Xyz to ABC:: Xyz
    re.compile(r'\:\:(?=[A-Z][a-z0-9]|[a-z][A-Z])')
)
PTN_SPLIT_LEFT.append(
    # Split 'ABC;DEF' to 'ABC; DEF'
    re.compile(r';(?! )')
)
PTN_SPLIT_LEFT.append(
    # Split hash number like #123 to # 123
    re.compile(r'#(?=[0-9]+)')
)
PTN_SPLIT_LEFT.append(
    # Split ip/mac address like address:xx to address: xx
    re.compile(r'address:(?=[0-9a-fA-F])')
)
PTN_SPLIT_LEFT.append(
    # Change something like (xx) to ( xx)
    re.compile(r'\((?=(\w|[-+]))')
)
PTN_SPLIT_LEFT.append(
    # Change something like [xx] to [ xx]
    re.compile(r'\[(?=(\w|[-+]))')
)
PTN_SPLIT_LEFT.append(
    # Split something like 5ms to 5 ms
    re.compile(r'\d+(?=(ms))')
)

PTN_SPLIT_RIGHT.append(
    # Split Change something like (xx) to (xx )
    re.compile(r'(?<=\w)\)')
)
PTN_SPLIT_RIGHT.append(
    # Split Change something like [xx] to [xx ]
    re.compile(r'(?<=\w)\]')
)

#----------------------------------------------------------------------------------------
# Pattern for adding session label 'segsign: '
#----------------------------------------------------------------------------------------
PTN_SESSION = re.compile(
    r'Loading compressed image \d|'
    r'Moving to Downstream Frequency'
)

#----------------------------------------------------------------------------------------
# Pattern for segment labels, 'segsign: ' or 'cxxx '
#----------------------------------------------------------------------------------------
PTN_LABEL = re.compile(
    r'(segsign: )|(c[0-9]{3} )'
)


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
in_log_table = False
in_log_block = False
in_log_block2 = False
in_log_block3 = False
in_log_block4 = False
last_line_empty = False
con_empty_ln_cnt = 0
last_label_removed = False
last_label = ''

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
#        RESERVE_TS = PTN_MAIN_TS.match(line)
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
    matchTS = PTN_MAIN_TS.match(line)
    if RESERVE_TS and matchTS:
        # Strip off the main timestamp including train and session labels if any exist
        currentLineTS = matchTS.group(0)
        if (DLOGCONTEXT or OSSCONTEXT or LLABCONTEXT) and ((not TRAINING) and (not METRICSEN)) \
            and (not PTN_FUZZY_TIME.search(currentLineTS)):
            if _idx == 0:
                heading_clean = True
            continue
        newline = PTN_MAIN_TS.sub('', line, count=1)
        # Inherit segment labels (segsign: or cxxx) from last labeled line if it is removed
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN) and last_label_removed:
            currentLineTS += last_label
            # Reset
            last_label_removed = False
            last_label = ''
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
        and (PTN_NESTED_LINE.match(newline) or newline in ['\n', '\r\n']):
        heading_clean = True
        # Take care if the removed line has segment label. Hand it to the next line
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN):
            label_match = PTN_LABEL.search(currentLineTS)
            if label_match:
                last_label = label_match.group(0)
                last_label_removed = True
        continue
    if heading_clean:
        heading_clean = False

    #-------------------------------------------------------------------
    # No STB timestamp and train label at start of each line in the
    # remaining of the loop
    #-------------------------------------------------------------------

    # Because of host system code bug of no endl, some primary logs are
    # concatenated to the former one. Split them and only reserve the
    # last log in the same line. Skip the match at position 0 if exits
    # as I will remove it later.
    if PTN_BFC_TS.search(newline, 2):
        match_g = PTN_BFC_TS.finditer(newline, 2)
        *_, last_match = match_g
        newline = newline[last_match.start() :]

    # Remove other timestamps, console prompts and others unwanted chars
    newline = PTN_CLEAN_CHAR.sub('', newline)

    # Remove unwanted log blocks
    if PTN_BLOCK_RM_START.match(newline):
        in_log_block = True
        # Delete current line
        # Update for the next line
        last_line_empty = False
        continue
    if in_log_block:
        if PTN_BLOCK_RM_END.match(newline):
            in_log_block = False
        else:
            # Delete current line
            # Update for the next line
            last_line_empty = False
            continue

    # Remove line starting with specific patterns
    if PTN_LINE_RM.match(newline):
        # If the removed line has segment label. Hand it to next line
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN):
            label_match = PTN_LABEL.search(currentLineTS)
            if label_match:
                last_label = label_match.group(0)
                last_label_removed = True
        # Update for the next line
        last_line_empty = False
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
    elif inDsChStatTable and in_log_table:
        if (not PTN_NESTED_LINE.match(newline)) and (newline not in ['\n', '\r\n']):
            # The table is messed by printings from other thread if we run into here
            # The normal DS channel status row should be nested by default. The messed
            # table might have empty lines in the middle of table
            tableMessed = True
            # Remove this line here, do not leave it to the "Remove table block"
            # Update for the next line
            last_line_empty = False
            continue
        elif newline in ['\n', '\r\n'] and dsTableEntryProcessed and (not lastLineMessed):
            # Suppose table ended with empty line but need also consider the case of
            # messed table. The 'dsTableEntryProcessed', 'lastLineMessed' and 'tableMessed'
            # are used here to process the messed table case.
            # Leave reset of 'in_log_table' to the "Remove table block"
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
    elif inUsChStatTable and in_log_table:
        if newline in ['\n', '\r\n']:
            # Suppose table ended with empty line
            # Leave reset of in_log_table to the remove table block
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
    if PTN_TABLE_TITLE_COMMON.match(newline):
        in_log_table = True
        # Update for the next line
        last_line_empty = False
        continue
    if in_log_table:
        if newline in ['\n', '\r\n']:
            # Suppose table ended with empty line
            # Note: we also reset the in_log_table for the DS/US channel status table above
            if (not inDsChStatTable) or (inDsChStatTable and dsTableEntryProcessed and (not lastLineMessed)):
                in_log_table = False
        elif not (inDsChStatTable or inUsChStatTable):
            # Still table line, remove it
            # Update for the next line
            last_line_empty = False
            continue

    # Remove title line of specific tables
    if PTN_TABLE_TITLE.match(newline):
        # Update for the next line
        last_line_empty = False
        continue

    # Indent some specific lines
    if PTN_PRI_TO_NESTED.match(newline):
        # Indent this line
        newline = ' ' + newline

    # Indent a block of lines from primary to embedded
    # Note: Do not indent the first line.
    # Empty line ends the block.
    if PTN_BLOCK_INDENT.match(newline):
        in_log_block3 = True
    elif in_log_block3:
        # Empty line ends the block
        if newline in ['\n', '\r\n']:
            in_log_block3 = False
        else:
            newline = ' ' + newline

    # Indent a block of lines from primary to embedded
    # Note: Do not indent the first line.
    # Special line (inclusive) ends the block.
    if PTN_BLOCK_INDENT2.match(newline):
        in_log_block4 = True
    elif in_log_block4:
        if PTN_BLOCK_INDENT2_END.match(newline):
            # Special line ends the block
            newline = ' ' + newline
            in_log_block4 = False
        else:
            newline = ' ' + newline

    # It is time to remove empty line
    if newline in ['\n', '\r\n']:
        if not last_line_empty:
            con_empty_ln_cnt = 1
        else:
            con_empty_ln_cnt += 1

        # Take care if the removed line has segment label. Hand it to the next line
        if (DLOGCONTEXT or LLABCONTEXT) and (TRAINING or METRICSEN):
            label_match = PTN_LABEL.search(currentLineTS)
            if label_match:
                last_label = label_match.group(0)
                last_label_removed = True

        # Update last_line_empty for the next line processing
        last_line_empty = True
        continue

    # Convert a nested line as primary if two more empty lines proceeded
    if PTN_NESTED_LINE.match(newline):
        if last_line_empty and (con_empty_ln_cnt >= 2):
            # Try to see if there are any exceptions
            if not PTN_NESTED_LINE_EXCEPTION.match(newline):
                newline = newline.lstrip()

    # Convert some specific nested lines as primary
    if PTN_NESTED_TO_PRI.match(newline):
        newline = newline.lstrip()

    # Remove specific whole multi-line log
    if PTN_BLOCK_RM_PRI.match(newline):
        in_log_block2 = True
        # Delete current line
        # Update for the next line
        last_line_empty = False
        continue
    if in_log_block2:
        if not PTN_NESTED_LINE.match(newline):
            in_log_block2 = False
        else:
            # Delete current line
            # Update for the next line
            last_line_empty = False
            continue

    # Split some tokens apart
    for ptn_obj in PTN_SPLIT_LEFT:
        m = ptn_obj.search(newline)
        if m:
            newline = ptn_obj.sub(m.group(0)+' ', newline)

    for ptn_obj in PTN_SPLIT_RIGHT:
        m = ptn_obj.search(newline)
        if m:
            newline = ptn_obj.sub(' '+m.group(0), newline)

    #--------------------------------------------------------------
    # Add session label 'segsign: ' for DeepLog
    # In DeepLog train or validation, we use the multi-session logs
    # METRICSEN means we do validation on the test dataset or not
    #--------------------------------------------------------------
    if DLOGCONTEXT and (TRAINING or METRICSEN):
        if PTN_SESSION.match(newline):
            newline = 'segsign: ' + newline

    # Update last_line_empty for the next line processing
    last_line_empty = False

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
    matchTS = PTN_MAIN_TS.match(line)
    if RESERVE_TS and matchTS:
        currentLineTS = matchTS.group(0)
        newline = PTN_MAIN_TS.sub('', line, count=1)
    else:
        newline = line

    if PTN_NESTED_LINE.match(newline):
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
