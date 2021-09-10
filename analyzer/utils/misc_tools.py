# Licensed under the MIT License - see LICENSE.txt
""" Miscellaneous tools for debugging, cleaning logs, etc. """
import os
from typing import List
import pickle
import collections
import pandas as pd
import analyzer.utils.data_helper as dh


__all__ = [
    "sort_tmplt_lib",
    "check_duplicates",
    'find_logs_by_eid',
]


def sort_tmplt_lib():
    """ Sort the template id for debugging """
    sorted_tmplt_lib = os.path.join(dh.TMP_DATA, 'template_lib_sorted.csv')

    data_df = pd.read_csv(dh.TEMPLATE_LIB)
    sorted_df = data_df.sort_values(by=['EventId'], ascending=True)

    sorted_df.to_csv(sorted_tmplt_lib, index=False)


def check_duplicates(folder: str, file: str):
    """ Check duplicate lines in a file """
    file_loc: str = os.path.join(dh.ANALYZER_DATA, folder, dh.LOG_TYPE, file)
    with open(file_loc, 'r', encoding='utf-8') as fout:
        ele: List[str] = fout.readlines()

    print({item: count for item, count in collections.Counter(ele).items() if count > 1})


def find_logs_by_eid(event_id: str, training: str):
    """ Find logs by event id in the structed log file """
    fzip: dict = dh.get_files_io()

    # Load structured file
    data_df = pd.read_csv(fzip['struct'], engine='c',
                          na_filter=False, memory_map=True)

    eid_logs = data_df['EventId'].tolist()

    if training:
        time_logs = data_df['Time'].tolist()
    else:
        # For prediction, use 1 based line number instead of timestamp
        time_logs = list(range(data_df.shape[0]))
        # Load map file between norm and raw
        with open(fzip['map_norm_raw'], 'rb') as fin:
            map_norm_raw = pickle.load(fin)

    # Do not iterate dataframe using data_df.iterrows(). It's very slow.
    for time, eid in zip(time_logs, eid_logs):
        if eid == event_id:
            if training:
                print(time, eid)
            else:
                print(map_norm_raw[time], eid)
