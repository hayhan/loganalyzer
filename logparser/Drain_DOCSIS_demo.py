#!/usr/bin/env python3
import os
from Drain_DOCSIS import LogParser

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
input_dir  = parentdir + '/logs/'  # The input directory of log file
output_dir = parentdir + '/results/'  # The output directory of parsing results
log_file   = 'test_norm.txt'  # The input log file name
log_format = '<Content>'  # DOCSIS log format

# Regular expression list for optional preprocessing (default: [])
regex      = [
    r'([A-Fa-f0-9]+\:){5}[A-Fa-f0-9]+',  # MAC Address
    r'(/|)([0-9]+\.){3}[0-9]+(:[0-9]+|)(:|)',  # IP Address
    #r'(?<=[^A-Za-z0-9])(\-?\+?\d+)(?=[^A-Za-z0-9])|[0-9]+$|0x[A-Fa-f0-9]+',  # Numbers
    r'0x[A-Fa-f0-9]+|(?<=[^A-Za-z0-9])(\-?\+?\d+\.?(\d+)?)'  # Numbers
    #r' [A-Fa-f0-9][A-Fa-f0-9] '
]
st         = 0.5  # Similarity threshold
depth      = 4  # Depth of all leaf nodes

parser = LogParser(log_format, indir=input_dir, outdir=output_dir,  depth=depth, st=st, rex=regex)
parser.parse(log_file)