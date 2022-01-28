# Licensed under the MIT License - see LICENSE.txt
""" The re patterns for parser module. LOG_TYPE specific.
"""
import re
import analyzer.utils.misc_regex as ptn


__all__ = [
    "PTN_HARD_PARA",
    "PTN_SPEC_TOKEN",
]


#
# Regular expression dict for optional preprocessing (can be empty {})
# Compiling ptnobj_p0~6 into a big one will slow down the preprocess
#

ptnobj_p0 = ptn.PTN_LIBC_CTIME
ptnobj_p1 = ptn.PTN_SNMP_MIB
ptnobj_p2 = ptn.PTN_MAC_ADDR
ptnobj_p3 = ptn.PTN_IP_V4
ptnobj_p4 = ptn.PTN_IP_V6

ptnobj_p5 = re.compile(
    # The filename string of image
    r'(?<= Filename: )\S+|'
    # OFDM channels CH32 and CH33, maybe different for 3391 and later
    r'C[hH]\d{2}|'
    # QAM/FEC lock status
    r'(?<= )((QAM|FEC) lock failure)|'
    # priDcid, dcid and prof list like priDcid= [ 197 26 1 ], etc.
    r'(?<=([Dd]cid= )|(prof= ))\[[^\]]*\]|'
    # Time format of 24-hour, e.g. 12:34:56
    r'(?<= )(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00)(?= |$)'
)

ptnobj_p6 = re.compile(
    # List of intergers and tuples like xxx = 1 2 3 4, (12-11.1) (10-11)
    # as well as Numbers including hex, decimal and integer.
    r'(?<=value=)(( [a-f0-9]{2}){6,14})'
    r'|(?<=HEX:)([A-F0-9]{2} )+'
    r'|( \( \d+\.?(\d+)?-\d+\.?(\d+)? \))+|( \d+){2,}|0x[A-Fa-f0-9]+'
    r'|(?<=[^A-Za-z0-9\.])(\-?\+?\d+\.?(\d+)?\*?)|(?<=\.\.)(\d+)'
)

ptnobj_p7 = re.compile(
    r'\( k[A-Z]\w+ \)|\( [du]cid \)|\( ErrorRecovery \)'
    r'|\( ConsoleCmdOverride \)|\( T4NoStationMaintTimeout \)'
    r'|\( T2NoInitMaintTimeout \)|\( not specified \)'
)

ptnobj_p8 = re.compile(r'Stat= (Continue|Success|Abort)')
ptnobj_p9 = re.compile(r'qam [yn] fec [yn] snr')
ptnobj_p10 = re.compile(r'txdata [yn]')

PTN_HARD_PARA= {
    ptnobj_p0: '<*>',
    ptnobj_p1: '<*>',
    ptnobj_p2: '<*>',
    ptnobj_p3: '<*>',
    ptnobj_p4: ' <*>',
    ptnobj_p5: '<*>',
    ptnobj_p6: ' <*>',
    ptnobj_p7: '( <*> )',
    ptnobj_p8: 'Stat= <*>',
    ptnobj_p9: 'qam <*> fec <*> snr',
    ptnobj_p10: 'txdata <*>',
}

#
# Regular expression list for special tokens, we want the special tokens
# are same between template and accepted log at the corresponding offset
#
ptnobj_s0 = re.compile(r'[a-zA-Z]+[0-9]*[a-zA-Z]*\:')
ptnobj_s1 = re.compile(r'[a-zA-Z]+\=')
ptnobj_s2 = re.compile(r'\(')
ptnobj_s3 = re.compile(r'\)')

PTN_SPEC_TOKEN = [
    ptnobj_s0,
    ptnobj_s1,
    ptnobj_s2,
    ptnobj_s3,
]
