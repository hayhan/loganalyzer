# Licensed under the MIT License - see License.txt
""" Base class of preprocess. Common for all LOG_TYPEs.
"""
import re
import os
import sys
import pickle
import shutil
from abc import ABC, abstractmethod
from typing import List, Pattern, Match
import logging
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh
from . import patterns as ptn

__all__ = [
    "PreprocessBase",
]


log = logging.getLogger(__name__)

class PreprocessBase(ABC):
    """ The base class of preprocess. """
    # pylint:disable=too-many-instance-attributes
    def __init__(self):
        self.fzip: dict = dh.get_files_preprocess()
        self.datatype: str = dh.get_data_type()
        self.training: bool = GC.conf['general']['training']
        self.metrics: bool = GC.conf['general']['metrics']
        self.context: str = GC.conf['general']['context']
        self.max_line: int = GC.conf['general']['max_line']

        self._rawlogs: List[str] = []
        self._newlogs: List[str] = []
        self._normlogs: List[str] = []
        self.labelvec: List[str] = []

        # The main timestamp flag. The default offset value is from
        # the standard format
        self._reserve_ts: bool = True
        self._log_head_offset: int = GC.conf['general']['head_offset']
        self.ptn_main_ts : Pattern = ptn.PTN_STD_TS

        # For prediction only. Does not include Loglizer.
        if not self.training:
            self.raw_ln_idx_new: List[int] = []
            self.raw_ln_idx_norm: List[int] = []


    def load_raw_logs(self):
        """ Read raw data file into memory """
        #
        # Raw log usually comes from serial console tools like SecureCRT
        # and probably the text file encoding is utf-8 (with BOM). See
        # https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8
        #
        # To skip the BOM when decoding the file, use utf-8-sig codec.
        # https://docs.python.org/3/library/codecs.html
        #
        with open(self.fzip['raw'], 'r', encoding='utf-8-sig') as rawfile:
            self._rawlogs = rawfile.readlines()


    def _main_timestamp_regx(self):
        """ Get timestamp regx pattern object. """
        if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
            and not (self.training or self.metrics):
            self.ptn_main_ts = re.compile(r'.{%d}' % self._log_head_offset)
        else:
            self.ptn_main_ts = ptn.PTN_STD_TS


    def _get_timestamp_info(self):
        """ Get updated timestamp info. """
        if self._log_head_offset > 0:
            self._reserve_ts = True
        elif self._log_head_offset == 0:
            self._reserve_ts = False
        else:
            # Not a LOG_TYPE log file
            sys.exit("It looks not {} log!".format(dh.LOG_TYPE))
        # Update main timestamp pattern object
        self._main_timestamp_regx()


    @staticmethod
    def _hand_over_label(curr_line_ts: str):
        """ There are cases that log with segment label is removed.
            Hand over the labe to the next line/log.
        """
        label_match: Match[str] = ptn.PTN_SEG_LABEL.search(curr_line_ts)
        if label_match:
            last_label: str = label_match.group(0)
            last_label_removed: bool = True
        return last_label, last_label_removed


    @property
    def log_head_offset(self):
        """ Get log head offset info. """
        return self._log_head_offset


    @log_head_offset.setter
    def log_head_offset(self, head_offset: int):
        """ Set log head offset info.
            Timestamp learnning will set the log_head_offset member.
            Update the value in config file and in-memory as well?
            \b
            - offset == -1: Not valid log file for LOG_TYPE
            - offset ==  0: Valid log file without timestamp
            - offset >   0: Valid log file with timestamp
        """
        self._log_head_offset = head_offset


    @property
    def normlogs(self):
        """ Get norm logs. """
        return self._normlogs


    @abstractmethod
    def preprocess_ts(self):
        """ Preprocess before learning timestamp width.
            Only for prediction of (OSS, DeepLog or Loglab).
            Not for Loglizer as it requires timestamps for windowing.
        """


    @abstractmethod
    def preprocess_new(self):
        """ Preprocess to generate the new log data.
            Clean the raw log data.
        """


    def preprocess_norm(self): # pylint: disable=too-many-branches
        """ Preprocess to generate the norm log data.
            Normalize the new log data, aka. converting multi-line log
            to one line.
            \b
            Note: Overwrite this func if multi-line log has a different
            format instead of primary/nested combination.
        """
        # Reset normlogs in case it is not empty
        self._normlogs = []

        if GC.conf['general']['aim']:
            newlogs = self._newlogs
        else:
            with open(self.fzip['new'], 'r', encoding='utf-8') as newfile:
                newlogs = newfile.readlines()

        #-------------------------------
        # Local state variables
        #-------------------------------
        # The last_line is initialized as empty w/o LF or CRLF
        last_line = ''
        last_line_ts = ''

        #
        # Concatenate nested line to its parent (primary) line
        #
        for idx, line in enumerate(newlogs):

            match_ts = self.ptn_main_ts.match(line)
            if self._reserve_ts and match_ts:
                curr_line_ts = match_ts.group(0)
                newline = self.ptn_main_ts.sub('', line, count=1)
            else:
                newline = line

            if ptn.PTN_NESTED_LINE.match(newline):
                # Concatenate current line to last_line. rstrip() will
                # strip LF or CRLF too
                last_line = last_line.rstrip()
                last_line += ', '
                last_line += newline.lstrip()
            else:
                # If current is primary line, then concatenating ends
                if self._reserve_ts and match_ts and (last_line != ''):
                    last_line = last_line_ts + last_line
                self._normlogs.append(last_line)

                # The raw line index list based on the norm file.
                # Mapping: norm file line index (0-based) -> test file
                # line index (1-based)
                # Do it only for prediction in DeepLog/Loglab and OSS
                if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                    and not (self.training or self.metrics):
                    self.raw_ln_idx_norm.append(self.raw_ln_idx_new[idx])

                # Update last line parameters
                last_line = newline
                if self._reserve_ts and match_ts:
                    last_line_ts = curr_line_ts

        # Write the last line of norm dataset
        if self._reserve_ts and match_ts and (last_line != ''):
            last_line = last_line_ts + last_line
        self._normlogs.append(last_line)

        # Conditionally save the normlogs and rawln idx to files per the
        # config file
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'w', encoding='utf-8') as fnorm:
                fnorm.writelines(self._normlogs)

            if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                and not (self.training or self.metrics):
                with open(self.fzip['rawln_idx'], 'wb') as fridx:
                    pickle.dump(self.raw_ln_idx_norm, fridx)


    def extract_labels(self):
        """ Extract the abnormal label vector from norm data.
            Use cases:
            1) Template generation from scratch
            2) Loglizer training and validation
            3) DeepLog validation
            Note:
            Do not call this func for predition
        """
        linecount: int = 0
        norm_logs: List[str] = []

        if not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'r', encoding='utf-8') as fnorm:
                self._normlogs = fnorm.readlines()

        for line in self._normlogs:
            try:
                # Suppose the standard timestamp
                match = ptn.PTN_ABN_LABEL.search(line, 24, 29)
                if match:
                    self.labelvec.append('a')
                    newline = ptn.PTN_ABN_LABEL.sub('', line, count=1)
                else:
                    self.labelvec.append('-')
                    newline = line

                linecount += 1
                # Label is removed
                norm_logs.append(newline)
            except Exception:  # pylint: disable=broad-except
                pass

        # Overwrite the old norm data with contents that labels removed
        self._normlogs = norm_logs

        # Save norm data and abnormal label vector to files per config
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'w+', encoding='utf-8') as fnorm:
                fnorm.writelines(self._normlogs)

            if self.context in ['LOGLIZER', 'DEEPLOG']:
                # _ToDo: Use other format instead of pandas dataframe
                # pylint: disable=import-outside-toplevel
                import pandas as pd
                logdf = pd.DataFrame(self.labelvec, columns=['Label'])
                logdf.insert(0, 'LineId', None)
                logdf['LineId'] = [i + 1 for i in range(linecount)]
                logdf.to_csv(self.fzip['label'], index=False)


    def cat_files_lst(self, raw_dir: str, file_names: List[str]):
        """ Cat multi raw log files in the file list under raw_dir
            into a monolith. Monolith file is either data/train.txt
            or data/test.txt based on the config settings.
        """
        raw_in_lst: List[str] = []
        with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
            for fname in file_names:
                raw_in_lst.append(os.path.join(raw_dir, fname))
            for rawf in raw_in_lst:
                with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                    shutil.copyfileobj(rawin, monolith)
                    # Add newline if no one at end of preceding file
                    monolith.write('\n')


    def cat_files_dir(self, raw_dir: str):
        """ Cat all raw log files under raw_dir (including sub-dirs)
            into a monolith for template gen / update and Loglizer.
            Monolith file is either data/train.txt or data/test.txt
            based on the config settings.
        """
        with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
            for dirpath, _, files in sorted(os.walk(raw_dir, topdown=True)):
                # print(f'Found directory: {dirpath}')
                for filename in files:
                    if filename in dh.SKIP_FILE_LIST:
                        continue
                    rawf = os.path.join(dirpath, filename)
                    # print(rawf)
                    with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                        shutil.copyfileobj(rawin, monolith)
                        # Add newline if no one at end of preceding file
                        monolith.write('\n')


    def cat_files_deeplog(self, raw_dir: str):
        """ Cat all raw log files under raw_dir (including sub-dirs)
            into a monolith. This is used for DeepLog training and
            validation by considering session labels. Monolith is either
            data/train.txt or data/test.txt based on the config settings
        """
        with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
            for dirpath, _, files in sorted(os.walk(raw_dir, topdown=True)):
                # print(f'Found directory: {dirpath}')
                for filename in files:
                    if filename in dh.SKIP_FILE_LIST:
                        continue
                    rawf = os.path.join(dirpath, filename)
                    # print(rawf)
                    with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                        for idx, line in enumerate(rawin):
                            # Insert 'segsign: ' to the start line of
                            # each file
                            if idx == 0:
                                match_ts = ptn.PTN_STD_TS.match(line)
                                if match_ts:
                                    curr_line_ts = match_ts.group(0)
                                    newline = ptn.PTN_STD_TS.sub('', line, count=1)
                                    line = curr_line_ts + 'segsign: ' + newline
                                else:
                                    print("Error: The timestamp is wrong!")
                            monolith.write(line)
                        monolith.write('\n')


    def cat_files_loglab(self):
        """ Cat all raw log files under raw_dir (including sub-dirs)
            into a monolith. Extract class names. This is used for
            Loglab training. Monolith is data/train.txt
        """
        with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
            loglab_dir = os.path.join(dh.RAW_DATA, 'loglab')
            # Note: name the class folder as 'cxxx', and training log
            # files in it as '*_xxx.txt'. Concatenate files under dir
            # data/raw/LOG_TYPE/loglab/c001/ ... /cxxx/.
            for dirpath, _, files in sorted(os.walk(loglab_dir, topdown=True)):
                # print(f'Found directory: {dirpath}')
                # Extract class name (sub-folder cxxx, dirpath[-4:])
                classname = re.split(r'[\\|/]', dirpath.strip('[\\|/]'))[-1]
                if not ptn.PTN_CLASS_LABEL.match(classname):
                    # Skip loglab itself and non-standard class name
                    # sub-folders if any exists.
                    continue
                # Sort the files per the file name string[-7:-4], aka.
                # the 3 digits num part.
                for filename in sorted(files, key=lambda x:x[-7:-4]):
                    rawf = os.path.join(dirpath, filename)
                    # print(rawf)
                    with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                        for idx, line in enumerate(rawin):
                            # Insert class_name to the start line of
                            # each file
                            if idx == 0:
                                match = ptn.PTN_STD_TS.match(line)
                                if match:
                                    curline_ts = match.group(0)
                                    newline = ptn.PTN_STD_TS.sub('', line, count=1)
                                    line = curline_ts + classname + ' ' + newline
                                else:
                                    print("Error: The timestamp is wrong!")
                            monolith.write(line)
                        monolith.write('\n')
