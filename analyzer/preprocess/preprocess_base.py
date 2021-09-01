# Licensed under the MIT License - see LICENSE.txt
""" Base class of preprocess. Common for all LOG_TYPEs.
"""
import re
import os
import sys
import pickle
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
        self.fzip: dict = dh.get_files_io()
        self.datatype: str = dh.get_data_type()
        self.training: bool = GC.conf['general']['training']
        self.metrics: bool = GC.conf['general']['metrics']
        self.context: str = GC.conf['general']['context']
        self.max_line: int = GC.conf['general']['max_line']

        self._rawlogs: List[str] = []
        self._newlogs: List[str] = []
        self._normlogs: List[str] = []
        self._labels: List[int] = []
        self._segdl: List[int] = []
        self._segll: List[tuple] = []

        # The main timestamp flag. The default offset value is from
        # the standard format
        self._reserve_ts: bool = True
        self._log_head_offset: int = GC.conf['general']['head_offset']
        self.ptn_main_ts : Pattern = ptn.PTN_STD_TS

        # For prediction only. Does not include Loglizer.
        if not self.training:
            self._map_new_raw: List[int] = []
            self._map_norm_raw: List[int] = []


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
        # In other modules, we more likely change the global config
        # setting. So sync it here.
        self._log_head_offset = GC.conf['general']['head_offset']

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
        """
        There are cases that log with segment label is removed. Hand
        over the labe to the next line/log.
        """
        last_label: str = ''
        last_label_removed: bool = False
        label_match: Match[str] = ptn.PTN_SEG_LABEL.search(curr_line_ts)
        if label_match:
            last_label = label_match.group(0)
            last_label_removed = True
        return last_label, last_label_removed


    @property
    def log_head_offset(self):
        """ Get log head offset info. """
        return self._log_head_offset


    @log_head_offset.setter
    def log_head_offset(self, head_offset: int):
        """
        Set log head offset info.
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


    @property
    def labels(self):
        """ Get the labels ('abn: ') vector. """
        return self._labels


    @property
    def map_norm_raw(self):
        """ Get the raw line index in norm data """
        return self._map_norm_raw


    @property
    def segdl(self):
        """ Get the segment info of deeplog """
        return self._segdl


    @property
    def segll(self):
        """ Get the segment info of loglab """
        return self._segll


    @abstractmethod
    def preprocess_ts(self):
        """
        Preprocess before learning timestamp width.
        Only for prediction of (OSS, DeepLog or Loglab).
        Not for Loglizer as it requires timestamps for windowing.
        """


    @abstractmethod
    def preprocess_new(self):
        """
        Preprocess to generate the new log data. Clean the raw log data.
        """


    def preprocess_norm(self): # pylint: disable=too-many-branches
        """
        Preprocess to generate the norm log data.
        Normalize the new log data, aka. converting multi-line log to
        one line.
        \b
        Note:
            Overwrite this func if multi-line log has a different format
            instead of primary/nested combination.
        """
        # Reset normlogs in case it is not empty
        self._normlogs = []

        if not GC.conf['general']['aim']:
            with open(self.fzip['new'], 'r', encoding='utf-8') as newfile:
                self._newlogs = newfile.readlines()

        # Make sure newlogs is not empty. Usually if the preprocess_new
        # thinks the timestamp format is abnormal, it will delete all
        # the lines and leads to an empty newlogs.
        assert len(self._newlogs) > 0

        #-------------------------------
        # Local state variables
        #-------------------------------
        # The last_line is initialized as empty w/o LF or CRLF
        last_line = ''
        last_line_ts = ''

        #
        # Concatenate nested line to its parent (primary) line
        #
        for idx, line in enumerate(self._newlogs):

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
                # Bypass appending the first empty line. This empty line
                # will be in the in-memory _normlogs although it will be
                # removed after writing to a file. It brings troubles to
                # the in-memory data in GlobalConfig['general']['aim']
                # enabled mode.
                if idx != 0:
                    self._normlogs.append(last_line)

                # The raw line index list based on the norm file.
                # Mapping: norm file line index (0-based) -> test file
                # line index (1-based)
                # Do it only for prediction in DeepLog/Loglab and OSS
                if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                    and not (self.training or self.metrics):
                    self._map_norm_raw.append(self._map_new_raw[idx])

                # Update last line parameters
                last_line = newline
                if self._reserve_ts and match_ts:
                    last_line_ts = curr_line_ts

        # Write the last line of norm dataset
        if self._reserve_ts and match_ts and (last_line != ''):
            last_line = last_line_ts + last_line
        self._normlogs.append(last_line)

        # Conditionally save the normlogs and rawln idx to files
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'w', encoding='utf-8') as fnorm:
                fnorm.writelines(self._normlogs)

            if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                and not (self.training or self.metrics):
                with open(self.fzip['map_norm_raw'], 'wb') as fridx:
                    pickle.dump(self._map_norm_raw, fridx)


    def extract_labels(self):
        """
        Extract the abnormal label vector from norm data.
        Use cases:
            1) Template generation from scratch
            2) Loglizer training and validation
            3) DeepLog validation
        Note:
            Do not call this func for predition
        """
        norm_logs: List[str] = []

        if not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'r', encoding='utf-8') as fnorm:
                self._normlogs = fnorm.readlines()

        for line in self._normlogs:
            try:
                # Suppose the standard timestamp
                match = ptn.PTN_ABN_LABEL.search(line, dh.STD_TIMESTAMP_LENGTH,
                        dh.STD_TIMESTAMP_LENGTH+dh.ABN_LABEL_LENGTH)
                if match:
                    self.labels.append(1)  # Abnormal
                    newline = ptn.PTN_ABN_LABEL.sub('', line, count=1)
                else:
                    self.labels.append(0)  # Normal
                    newline = line

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
                with open(self.fzip['labels'], 'wb') as fout:
                    pickle.dump(self._labels, fout)


    def cat_files_lst(self, raw_dir: str, file_names: List[str]):
        """
        Cat multi raw log files in the file list under raw_dir into a
        monolith. Based on the config settings, monolith file is either
        data/train.txt or data/test.txt .
        """
        raw_in_lst: List[str] = []
        self._rawlogs = []

        for fname in file_names:
            raw_in_lst.append(os.path.join(raw_dir, fname))
        for rawf in raw_in_lst:
            with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                self._rawlogs += rawin.readlines()
            # Get the last line of preceding file to check if the line
            # feed exists at the end.
            if self._rawlogs[-1][-1] != '\n':
                self._rawlogs[-1] += '\n'

        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
                monolith.writelines(self._rawlogs)


    def cat_files_dir(self, raw_dir: str):
        """
        Cat all raw log files under raw_dir (including sub-dirs) into a
        monolith for template gen / update and Loglizer. Monolith file
        is either data/train.txt or data/test.txt based on the config
        settings.
        """
        self._rawlogs = []

        for dirpath, _, files in sorted(os.walk(raw_dir, topdown=True)):
            # print(f'Found directory: {dirpath}')
            for filename in files:
                if filename in dh.SKIP_FILE_LIST:
                    continue
                rawf = os.path.join(dirpath, filename)
                # print(rawf)
                with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                    self._rawlogs += rawin.readlines()
                # Get the last line of preceding file to check if the
                # line feed exists at the end.
                if self._rawlogs[-1][-1] != '\n':
                    self._rawlogs[-1] += '\n'

        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
                monolith.writelines(self._rawlogs)


    def cat_files_deeplog(self, raw_dir: str):
        """
        Cat all raw log files under raw_dir (including sub-dirs) into a
        a monolith. This is used for DeepLog training and validation by
        considering session labels. Monolith is either data/train.txt or
        data/test.txt based on the config settings.
        """
        self._rawlogs = []

        for dirpath, _, files in sorted(os.walk(raw_dir, topdown=True)):
            # print(f'Found directory: {dirpath}')
            for filename in files:
                if filename in dh.SKIP_FILE_LIST:
                    continue
                rawf = os.path.join(dirpath, filename)
                # print(rawf)
                with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                    for idx, line in enumerate(rawin):
                        # Insert 'segsign: ' to start line of each file
                        if idx == 0:
                            match_ts = ptn.PTN_STD_TS.match(line)
                            if match_ts:
                                curr_line_ts = match_ts.group(0)
                                newline = ptn.PTN_STD_TS.sub('', line, count=1)
                                line = curr_line_ts + 'segsign: ' + newline
                            else:
                                print("Error: The timestamp is wrong!")
                        self._rawlogs.append(line)
                # Get the last line of preceding file to check if the
                # line feed exists at the end.
                if self._rawlogs[-1][-1] != '\n':
                    self._rawlogs[-1] += '\n'

        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
                monolith.writelines(self._rawlogs)


    def cat_files_loglab(self):
        """
        Cat all raw log files under raw_dir (including sub-dirs) into a
        monolith. Extract class names. This is used for Loglab training.
        Monolith is data/train.txt
        """
        self._rawlogs = []

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
                        self._rawlogs.append(line)
                # Get the last line of preceding file to check if the
                # line feed exists at the end.
                if self._rawlogs[-1][-1] != '\n':
                    self._rawlogs[-1] += '\n'

        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
                monolith.writelines(self._rawlogs)


    def segment_deeplog(self):
        """
        The label can be added by both file concatenation and preprocess
        of logparser. The same label might be added twice for the log at
        the beginging of each file. So we replace the labels with empty
        by max twice below.

        In test dataset for validation, the session label might not
        exist. Make sure we return the correct session vector (aka one
        element representing the session size) in this case.

        The segment info format: [segment_size, ...]
        """
        norm_logs: List[str] = []
        session_start: int = 0

        if not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'r', encoding='utf-8') as fnorm:
                self._normlogs = fnorm.readlines()

        for idx, line in enumerate(self._normlogs):
            # Standard format '[20190719-08:58:23.738] ' is always there
            match = ptn.PTN_SEG_LABEL_1.search(line, dh.STD_TIMESTAMP_LENGTH,
                    dh.STD_TIMESTAMP_LENGTH+dh.SEG_LABEL_LENGTH)
            if match:
                newline = ptn.PTN_SEG_LABEL_1.sub('', line, count=2)
                if idx != 0:
                    self._segdl.append(idx - session_start)
                    session_start = idx
            else:
                newline = line

            # Session label is removed
            norm_logs.append(newline)

        # The last session size
        self._segdl.append(len(self._normlogs) - session_start)
        # print(self._segdl)

        # Overwrite the old norm data
        self._normlogs = norm_logs

        # Conditionally save data to files per config file
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['segdl'], 'wb') as fout:
                pickle.dump(self._segdl, fout)

            with open(self.fzip['norm'], 'w+', encoding='utf-8') as fout:
                fout.writelines(self._normlogs)


    def segment_loglab(self):
        """
        The class label 'cxxx' was inserted at the first line of each
        file when generating the monolith training data/file. As each
        separate training file is one sample, we can get the size of
        each sample and the target class of the sample resides in.

        The segment info format: [(sample_size, sample_class), ...]
        sample_size is int type and unit is log, aka. one line in norm.
        sample_class is str type and is int after removing heading 'c'.
        """
        norm_logs: List[str] = []
        sample_start: int = 0

        if not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'r', encoding='utf-8') as fnorm:
                self._normlogs = fnorm.readlines()

        for idx, line in enumerate(self._normlogs):
            # Standard format '[20190719-08:58:23.738] ' is always there
            match = ptn.PTN_SEG_LABEL_2.search(line, dh.STD_TIMESTAMP_LENGTH,
                    dh.STD_TIMESTAMP_LENGTH+dh.CLASS_LABEL_LENGTH)
            if idx == 0 and not match:
                print("Something is wrong with the monolith file, exit!")
                sys.exit(1)
            elif match:
                classname = match.group(0).strip()
                newline = ptn.PTN_SEG_LABEL_2.sub('', line, count=1)
                norm_logs.append(newline)
                if idx == 0:
                    classname_last = classname
                    continue
                self._segll.append((idx - sample_start, classname_last))
                sample_start = idx
                classname_last = classname
            else:
                norm_logs.append(line)

        # The last segment/sample info
        self._segll.append((len(self._normlogs) - sample_start, classname_last))
        # print(self._segll)

        # Overwrite the old norm data
        self._normlogs = norm_logs

        # Conditionally save data to files per config file
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['segll'], 'wb') as fout:
                pickle.dump(self._segll, fout)

            with open(self.fzip['norm'], 'w+', encoding='utf-8') as fout:
                fout.writelines(self._normlogs)
