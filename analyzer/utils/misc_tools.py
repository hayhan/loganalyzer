# Licensed under the MIT License - see LICENSE.txt
""" Miscellaneous tools for debugging, cleaning logs, etc. """
import os
import re
from typing import List
from datetime import datetime
from importlib import import_module
import pickle
import collections
import pandas as pd
import analyzer.utils.data_helper as dh

# Load LOG_TYPE dependent helpers
msc = import_module("analyzer.extensions." + dh.LOG_TYPE + ".misc")


__all__ = [
    "sort_tmplt_lib",
    "check_duplicates",
    "find_logs_by_eid",
    "norm_timestamp",
]


def sort_tmplt_lib():
    """ Sort the template id for debugging """
    sorted_tmplt_lib = os.path.join(dh.TMP_DATA, 'template_lib_sorted.csv')

    data_df = pd.read_csv(dh.TEMPLATE_LIB)
    sorted_df = data_df.sort_values(by=['EventId'], ascending=True)

    sorted_df.to_csv(sorted_tmplt_lib, index=False)


def check_duplicates(strings: List[str]):
    """ Check duplicate lines in a txt file """
    dup_set: List[List[int]] = []
    for item, count in collections.Counter(strings).items():
        if count > 1 and item not in ['0\n']:
            indices = [i for i, x in enumerate(strings) if x == item]
            dup_set.append(indices)

    return dup_set


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


def norm_timestamp(rawfile: str, newfile: str, log_offset: int, dt_ts: float):
    """ Replace the timestamps with standard ones in a log file """
    # Pattern for old timestamp, aka. the log head offset
    pattern_timestamp = re.compile(rf'.{{{log_offset}}}')

    # Replace old timestamp (including no timestamp) with standard one.
    out_logs: List[str] = []
    with open(rawfile, 'r', encoding='utf-8-sig') as rawin:
        for line in rawin:
            if pattern_timestamp.match(line):
                dt_obj = datetime.fromtimestamp(dt_ts)
                # Finetune line below to match your case
                dt_format = \
                    msc.std_timestamp(dt_obj.strftime(msc.STD_TIMESTAMP_FORMAT))
                # Works even log_offset is zero, aka. no old timestamp.
                newline = pattern_timestamp.sub(dt_format, line, count=1)
                # Increase 100ms per line
                dt_ts += 0.100000
            else:
                # Messed lines, skip
                continue
            out_logs.append(newline)

    with open(newfile, 'w', encoding='utf-8') as fout:
        fout.writelines(out_logs)

    return dt_ts
