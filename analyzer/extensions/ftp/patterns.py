# Licensed under the MIT License - see LICENSE.txt
""" The re patterns for preprocess & parser modules. LOG_TYPE specific.
"""
import re
import analyzer.utils.misc_regex as ptn


__all__ = [
]


# ======================================================================
# Preprocess module
# ======================================================================

# ----------------------------------------------------------------------
# Patterns for main / standard timestamp
# ----------------------------------------------------------------------
PTN_STD_TS = re.compile(
    # Standard timestamp from Filezilla, e.g. 2022-06-22 14:42:53. Also
    # includes the process id and session id. Besides, we add Loglizer
    # Label, Deeplog segment sign, Loglab class label just behind the
    # timestamp. The two columns next to timestamp are process id and
    # session id, which will be removed in preprocess.
    # Example of complete log format as below:
    # 2022-06-22 14:42:53 10236 1 Command: AUTH TLS
    #
    r'\d{4}-\d{2}-\d{2} (([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) '
    r'(abn: )?(segsign: )?(c[0-9]{3} )?'
)

# ----------------------------------------------------------------------
# Patterns for timestamp, console prompt, thread tag and others
# ----------------------------------------------------------------------
PTN_CLEAN_CHAR = re.compile(
    # Process id and session id
    r'\d+ \d (?=[A-Z][a-z]+: )',

    re.IGNORECASE
)

# ----------------------------------------------------------------------
# Patterns for response status
# ----------------------------------------------------------------------
# Response 211 indicates system status
ptnobj_rsp_211 = re.compile(r'Response: 211[ \-]')
# Response 213 indicates file status
ptnobj_rsp_213 = re.compile(r'Response: 213 ')
# Response 220 indicates ftp server is ready
ptnobj_rsp_220 = re.compile(r'Response: 220[ \-]')
# Response 421 indicates service not available
ptnobj_rsp_421 = re.compile(r'Response: 421 ')

PTN_RSP_STAT = {
    ptnobj_rsp_211: "Response: 211 System status, or system help\n",
    ptnobj_rsp_213: "Response: 213 File status\n",
    ptnobj_rsp_220: "Response: 220 FTP server is ready\n",
    ptnobj_rsp_421: "Response: 421 Service not available, closing connection\n"
}

# ----------------------------------------------------------------------
# Patterns for spliting tokens. They cannot be built as a big one.
# ----------------------------------------------------------------------
# Split assignment token like ABC=xyz to ABC= xyz
ptnobj_l0 = re.compile(r'=(?=[^= \r\n])')
# Split cpp class token like ABC::Xyz to ABC:: Xyz
ptnobj_l1 = re.compile(r'\:\:(?=[a-zA-Z_]{3,})')
# Change something like (xx) to ( xx)
ptnobj_l2 = re.compile(r'\((?=(\w|[-+]))')

# Split Change something like (xx) to (xx )
ptnobj_r0 = re.compile(r'(?<=\w)\)')

PTN_SPLIT_LEFT = [
    ptnobj_l0, ptnobj_l1, ptnobj_l2,
]
PTN_SPLIT_RIGHT = [
    ptnobj_r0,
]

# ======================================================================
# Parser module
# ======================================================================

#
# Regular expression dict for optional preprocessing (can be empty {})
# Compiling ptnobj_p0~3 into a big one will slow down the preprocess
#

ptnobj_p0 = ptn.PTN_LIBC_CTIME
ptnobj_p1 = ptn.PTN_IP_V4
ptnobj_p2 = ptn.PTN_MAC_ADDR

ptnobj_p3 = re.compile(
    # Time format of 24-hour, e.g. 12:34:56
    r'(?<= )(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)(?= |$)'
)

ptnobj_p4 = re.compile(
    # List of intergers and tuples like xxx = 1 2 3 4, (12-11.1) (10-11)
    # as well as Numbers including hex, decimal and integer.
    # r'( \( \d+\.?(\d+)?-\d+\.?(\d+)? \))+|( \d+){2,}|0x[A-Fa-f0-9]+'
    # r'|(?<=[^A-Za-z0-9\.])(\-?\+?\d+\.?(\d+)?\*?)|(?<=\.\.)(\d+)'
    r' \d+ '
)

PTN_HARD_PARA = {
    ptnobj_p0: '<*>',
    ptnobj_p1: '<*>',
    ptnobj_p2: '<*>',
    ptnobj_p3: '<*>',
    ptnobj_p4: ' <*> ',
}

#
# Regular expression list for special tokens. We want special tokens are
# same between template and the accepted log at the corresponding offset
#
ptnobj_s0 = re.compile(r'[a-zA-Z_]+::')
ptnobj_s1 = re.compile(r'[a-zA-Z_]+\(\)')
ptnobj_s2 = re.compile(r'[a-zA-Z_]+\(')

PTN_SPEC_TOKEN = [
    ptnobj_s0,
    ptnobj_s1,
    ptnobj_s2,
]
