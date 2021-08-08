# Licensed under the MIT License - see License.txt
""" The re patterns for parser module. LOG_TYPE specific.
"""
import re

__all__ = [
    "PTN_HARD_PARA",
    "PTN_SPEC_TOKEN",
]


#
# Regular expression dict for optional preprocessing (can be empty {})
#

ptnobj_p0 = re.compile(
    # The libc ctime format
    r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun) '
    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) '
    r'(([0-2]\d)|(3[0-1])) '
    r'(([01]\d|2[0-3]):([0-5]\d):([0-5]\d)|24:00:00) \d{4}|'
    # SNMP MIB OID
    r'([0-9]+\.){4,20}[0-9]+|'
    # MAC Address
    r'([A-Fa-f0-9]+\:){5}[A-Fa-f0-9]+|'
    # IPv4 Address
    r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)|'
    # The filename string of image
    r'(?<= Filename: )\S+|'
    # OFDM channels CH32 and CH33, maybe different for 3391 and later
    r'CH\d{2}|'
    # QAM/FEC lock status
    r'(QAM lock failure)|(FEC lock failure)|'
    # IPv6 Address from https://gist.github.com/mnordhoff/2213179
    # A more elegant rex can be found at
    # https://gist.github.com/dfee/6ed3a4b05cfe7a6faf40a2102408d5d8
    r' (?:(?:[0-9A-Fa-f]{1,4}:){6}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}'
    r'|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]'
    r'|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
    r'|::(?:[0-9A-Fa-f]{1,4}:){5}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}'
    r'|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]'
    r'|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
    r'|(?:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]{1,4}:){4}'
    r'(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}'
    r'|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]'
    r'|25[0-5]))|(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]'
    r'{1,4}:){3}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]'
    r'|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}'
    r'|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:){,2}[0-9A-Fa-f]'
    r'{1,4})?::(?:[0-9A-Fa-f]{1,4}:){2}(?:[0-9A-Fa-f]{1,4}:[0-9A-Fa-f]{1,4}'
    r'|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.){3}(?:[0-9]'
    r'|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|(?:(?:[0-9A-Fa-f]{1,4}:)'
    r'{,3}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}:(?:[0-9A-Fa-f]{1,4}:'
    r'[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]'
    r'|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
    r'|(?:(?:[0-9A-Fa-f]{1,4}:){,4}[0-9A-Fa-f]{1,4})?::(?:[0-9A-Fa-f]'
    r'{1,4}:[0-9A-Fa-f]{1,4}|(?:(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]'
    r'|25[0-5])\\.){3}(?:[0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))'
    r'|(?:(?:[0-9A-Fa-f]{1,4}:){,5}[0-9A-Fa-f]{1,4})?::[0-9A-Fa-f]{1,4}'
    r'|(?:(?:[0-9A-Fa-f]{1,4}:){,6}[0-9A-Fa-f]{1,4})?::)(/\d{1,3})?|'
    # List of intergers and tuples like xxx = 1 2 3 4, (12-11.1) (10-11)
    # as well as Numbers including hex, decimal and integer.
    r'(?<=value=)(( [a-f0-9]{2}){14})'
    r'|(?<=HEX:)([A-F0-9]{2} )+'
    r'|( \( \d+\.?(\d+)?-\d+\.?(\d+)? \))+|( \d+){2,}|0x[A-Fa-f0-9]+'
    r'|(?<=[^A-Za-z0-9\.])(\-?\+?\d+\.?(\d+)?\*?)|(?<=\.\.)(\d+)'
)

ptnobj_p1 = re.compile(
    r'\( k[A-Z]\w+ \)|\( [du]cid \)|\( ErrorRecovery \)'
    r'|\( ConsoleCmdOverride \)|\( T4NoStationMaintTimeout \)'
    r'|\( T2NoInitMaintTimeout \)|\( not specified \)'
)

ptnobj_p2 = re.compile(r'Stat= (Continue|Success|Abort)')
ptnobj_p3 = re.compile(r'qam [yn] fec [yn] snr')
ptnobj_p4 = re.compile(r'txdata [yn]')

PTN_HARD_PARA= {
    ptnobj_p0: ' <*>',
    ptnobj_p1: '( <*> )',
    ptnobj_p2: 'Stat= <*>',
    ptnobj_p3: 'qam <*> fec <*> snr',
    ptnobj_p4: 'txdata <*>',
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
