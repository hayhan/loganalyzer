"""
Description : Sort template library per eventid column
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

import os
import pandas as pd

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

templib_loc = parentdir + '/results/persist/cm/template_lib.csv'
sorted_templib_loc = parentdir + '/tmp/template_lib_sorted.csv'

df = pd.read_csv(templib_loc)
sorted_df = df.sort_values(by=['EventId'], ascending=True)

sorted_df.to_csv(sorted_templib_loc, index=False)
