# Licensed under the MIT License - see LICENSE.txt
""" Miscellaneous tools for debugging, cleaning logs, etc. """
import os
import collections
import pandas as pd
import analyzer.utils.data_helper as dh

__all__ = [
    "sort_tmplt_lib",
    "check_duplicates",
]


def sort_tmplt_lib():
    """ Sort the template id for debugging """
    sorted_tmplt_lib = os.path.join(dh.TMP_DATA, 'template_lib_sorted.csv')

    data_df = pd.read_csv(dh.TEMPLATE_LIB)
    sorted_df = data_df.sort_values(by=['EventId'], ascending=True)

    sorted_df.to_csv(sorted_tmplt_lib, index=False)


def check_duplicates(folder, file):
    """ Check duplicates in list """
    file_loc = os.path.join(dh.ANALYZER_DATA, folder, dh.LOG_TYPE, file)
    with open(file_loc, 'r', encoding='utf-8') as fout:
        ele = fout.readlines()

    print({item: count for item, count in collections.Counter(ele).items() if count > 1})
