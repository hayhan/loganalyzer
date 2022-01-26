# Licensed under the MIT License - see LICENSE.txt
""" The re patterns for preprocess module. LOG_TYPE specific.
"""
import re


__all__ = [
    "PTN_BFC_TS",
    "PTN_CLEAN_CHAR",
    "PTN_FUZZY_TIME",
    "PTN_LINE_RM",
    "PTN_TABLE_TITLE",
    "PTN_NESTED_LINE",
    "PTN_NESTED_LINE_EXCEPTION",
    "PTN_PRI_TO_NESTED",
    "PTN_BLOCK_INDENT",
    "PTN_BLOCK_INDENT2",
    "PTN_BLOCK_INDENT2_END",
    "PTN_NESTED_TO_PRI",
    "PTN_BLOCK_RM_PRI",
    "PTN_BLOCK_RM_START",
    "PTN_BLOCK_RM_END",
    "PTN_TABLE_TITLE_COMMON",
    "PTN_DS_CHAN_TABLE_START",
    "PTN_DS_CHAN_TABLE_END",
    "PTN_US_CHAN_TABLE_START",
    "PTN_US_CHAN_TABLE_END",
    "PTN_SPLIT_LEFT",
    "PTN_SPLIT_RIGHT",
    "PTN_SPLIT_LEFT_TS",
    "PTN_SPLIT_RIGHT_TS",
    "PTN_SESSION",
]


# ----------------------------------------------------------------------
# Patterns for timestamp, console prompt, thread tag and others
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Pattern for fuzzy time format, e.g. 12:34:56, 12-34-56, 12/34/56, etc.
# ----------------------------------------------------------------------
PTN_FUZZY_TIME = re.compile(
    r'[0-5][0-9][^a-zA-Z0-9 ][0-5][0-9][^a-zA-Z0-9 ][0-5][0-9]'
)

# ----------------------------------------------------------------------
# Pattern for removing specific lines
# ----------------------------------------------------------------------
PTN_LINE_RM = re.compile(
    r'\*+$|BCM3390\d+|RAM Windows size \d+ mb|'
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

# ----------------------------------------------------------------------
# Pattern for removing Table headers
# ----------------------------------------------------------------------
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
    # r' *Active Downstream Channel Diagnostics|'
    # r' *rx id +dcid +freq|'
    # r' *plc +prfA|'
    # r' *Active Upstream Channels:|'
    # r' *rng +pwr|'
    # r' *txid +ucid +dcid +sid|'
    r' {5}US chan ID {5}Tx Power \(dBmV\)'
)

# ----------------------------------------------------------------------
# Pattern for empty line
# ----------------------------------------------------------------------
PTN_EMPTY_LINE = re.compile(
    r'^[ \t]*$'
)

# ----------------------------------------------------------------------
# Pattern for nested line
# ----------------------------------------------------------------------
PTN_NESTED_LINE = re.compile(
    r' +|\t+'
)

# ----------------------------------------------------------------------
# Pattern for nested line (exceptions)
# ----------------------------------------------------------------------
PTN_NESTED_LINE_EXCEPTION = re.compile(
    r' +Ranging state info:'
)

# ----------------------------------------------------------------------
# Pattern for indenting specific primary lines
# ----------------------------------------------------------------------
PTN_PRI_TO_NESTED = re.compile(
    r'Assigned OFDMA Data Profile IUCs|'
    r'fDestSingleTxTargetUsChanId|'
    r'fTmT4NoUnicastRngOpStdMlsec|'
    r'MSG PDU:|'
    r'to a CM prior to sending|'
    r'Load Address: '
)

# ----------------------------------------------------------------------
# Pattern for indenting a block/table of lines
# Run this before removing empty lines
# ----------------------------------------------------------------------

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
    r'Using per transmitter stored initial upstream power|'
    r'TCC ranging parameters specified power offset of'
)

# ----------------------------------------------------------------------
# Pattern for converting specific lines as primary
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Pattern for block of logs that should be removed entirely
# Block end condition: primary line (exclusive)
# ----------------------------------------------------------------------
PTN_BLOCK_RM_PRI = re.compile(
    r' {4}tap values:|'
    r' *Trimmed Downstream Ambiguity Resolution Frequency List'
)

# ----------------------------------------------------------------------
# Pattern for block of logs that should be removed entirely
# [BlockStart: inclusive, BlockEnd: exclusive)
# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
# Pattern for DS/US channel Tables
# ----------------------------------------------------------------------
PTN_TABLE_TITLE_COMMON = re.compile(
    # Common table title starting with "----", " ----" or "  ----"
    r' *----'
)

# DS/US channel status tables
PTN_DS_CHAN_TABLE_START = re.compile(r'Active Downstream Channel Diagnostics:')
PTN_DS_CHAN_TABLE_END = re.compile(r'\* indicates currently configured')
PTN_US_CHAN_TABLE_START = re.compile(r'Active Upstream Channels:')
# PTN_US_CHAN_TABLE_END = re.compile(r'Dynamic range window ')
PTN_US_CHAN_TABLE_END = re.compile(r'\S')

# ----------------------------------------------------------------------
# Patterns for spliting tokens. They cannot be built as a big one.
# ----------------------------------------------------------------------
# Split assignment token like ABC=xyz to ABC= xyz
ptnobj_l0 = re.compile(r'=(?=[^= \r\n])')
# Split cpp class token like ABC::Xyz to ABC:: Xyz
ptnobj_l1 = re.compile(r'\:\:(?=[A-Z][a-z0-9]|[a-z][A-Z])')
# Split 'ABC;DEF' to 'ABC; DEF'
ptnobj_l2 = re.compile(r';(?! )')
# Split hash number like #123 to # 123
ptnobj_l3 = re.compile(r'#(?=[0-9]+)')
# Split ip/mac address like address:xx to address: xx
ptnobj_l4 = re.compile(r'address:(?=[0-9a-fA-F])')
# Change something like (xx) to ( xx)
ptnobj_l5 = re.compile(r'\((?=(\w|[-+]))')
# Change something like [xx] to [ xx]
ptnobj_l6 = re.compile(r'\[(?=(\w|[-+]))')
# Split something like 5ms to 5 ms
ptnobj_l7 = re.compile(r'\d+(?=(ms))')

# Split Change something like (xx) to (xx )
ptnobj_r0 = re.compile(r'(?<=\w)\)')
# Split Change something like [xx] to [xx ]
ptnobj_r1 = re.compile(r'(?<=\w)\]')

PTN_SPLIT_LEFT = [
    ptnobj_l0, ptnobj_l1, ptnobj_l2, ptnobj_l3,
    ptnobj_l4, ptnobj_l5, ptnobj_l6, ptnobj_l7,
]
PTN_SPLIT_RIGHT = [
    ptnobj_r0, ptnobj_r1,
]

PTN_SPLIT_LEFT_TS = [
    ptnobj_l0, ptnobj_l1, ptnobj_l2, ptnobj_l5,
    ptnobj_l7,
]
PTN_SPLIT_RIGHT_TS = [
    ptnobj_r0,
]

# ----------------------------------------------------------------------
# Pattern for adding session label 'segsign: '
# ----------------------------------------------------------------------
PTN_SESSION = re.compile(
    r'Loading compressed image \d|'
    r'Moving to Downstream Frequency'
)
