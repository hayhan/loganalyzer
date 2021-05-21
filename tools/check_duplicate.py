"""
Description : Check duplicates in list
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import collections

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

file_loc = parentdir + '/results/persist/cm/event_id_loglab.txt'

file = open(file_loc, 'r')

a = file.readlines()

print({item: count for item, count in collections.Counter(a).items() if count > 1})
