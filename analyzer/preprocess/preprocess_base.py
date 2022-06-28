# Licensed under the MIT License - see LICENSE.txt
""" Base class of preprocess. Common for all LOG_TYPEs.
"""
import re
import os
import sys
import pickle
import logging
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Pattern, Match, Any, Dict
from tqdm import tqdm
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh
from . import patterns as ptn


__all__ = ["PreprocessBase"]

log = logging.getLogger(__name__)


# ---------------------------------------------
# Terminologies:
# primary line - no space proceeded
# nested line  - one or more spaces proceeded
# empty line   - LF or CRLF only in one line
# ---------------------------------------------

# pylint: disable=too-many-instance-attributes,too-many-public-methods
class PreprocessBase(ABC):
    """ The base class of preprocess. """
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
        self.ptn_main_ts: Pattern = ptn.PTN_STD_TS

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
        if not os.path.exists(self.fzip['raw']):
            print(f"The {dh.get_data_type()}.txt doesn't exist in cooked folder!!!")
            sys.exit(1)

        with open(self.fzip['raw'], 'r', encoding='utf-8-sig') as rawfile:
            self._rawlogs = rawfile.readlines()

    def _main_timestamp_regx(self):
        """ Get timestamp regx pattern object. """
        if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
            and not (self.training or self.metrics):
            self.ptn_main_ts = re.compile(rf'.{{{self._log_head_offset}}}')
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
            # Not a LOG_TYPE log file. It's OK to exit for console app.
            # But for webgui app, it's not good as no any info send to
            # later modules.
            # sys.exit(f"It looks not {dh.LOG_TYPE} log!")
            print(f"It looks not {dh.LOG_TYPE} log!")
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
    def process_for_domain(self, line: str, state: Dict[str, Any]):
        """
        Special line process for LOG_TYPE
        """

    def preprocess_ts(self):
        """
        Preprocess before learning timestamp width. Only for prediction
        of (OSS, DeepLog and Loglab). Not for Loglizer as it requires
        timestamps for windowing.
        \b
        Note:
            After light washing, need do two things. First, set the log
            offset value self._log_head_offset and GC.conf['general']
            ['head_offset'] to zero. Second, save the light washed logs
            to self._normlogs.
        """
        log.info("Preprocess before timestamp detection.")

        # Reset normlogs in case it is not empty
        self._normlogs = []

        for idx, line in enumerate(self._rawlogs):

            # Remove the NULL char '\0' at the first line if it exists
            if idx == 0 and line[0] == '\0':
                continue

            # Remove other timestamps, console prompt and unwanted chars
            # @abstractmethod: Override it in the derived class
            line = self.clean_misc_char(line)

            # Remove empty line
            # if line in ['\n', '\r\n', '']:
            if ptn.PTN_EMPTY_LINE.match(line):
                continue

            # Split some tokens apart
            # @abstractmethod: Override it in the derived class
            line = self.split_tokens(line, True)

            # Save directly as norm data for parsing / clustering
            self._normlogs.append(line)

            # Check only part of lines which are usually enough to
            # determine timestamp
            if idx >= self.max_line:
                break

        # Suppose the log head offset is always zero
        self._log_head_offset = 0
        GC.conf['general']['head_offset'] = 0

        # Conditionally save the normlogs to a file per the config file
        # Note: preprocess_norm will overwrite the normlogs
        self.cond_save_strings(self.fzip['norm'], self._normlogs)

    # pylint: disable=too-many-statements, disable=too-many-branches
    def preprocess_new(self):
        """
        Preprocess to generate the new log data. Clean the raw log data.
        \b
        Note:
            After heavy washing, need do two things. First, save index
            mapping between raw and new logs to self._map_new_raw. Next,
            save the heavy washed logs to self._newlogs.
        """
        log.info("Preprocess to generate new log data.")
        # For prediction, the timestamp in the test log is unknown or
        # even does not exist. The preprocess will try to learn the
        # width of the unknown timestamp in advance. So here get the
        # updated info instead of the default one in config file.
        self._get_timestamp_info()
        # Bail out early for the wrong LOG_TYPE
        if self._log_head_offset < 0:
            return

        # Reset newlogs in case it is not empty
        self._newlogs = []

        #-------------------------------
        # Local state variables
        #-------------------------------
        stat: Dict[str, Any] = {
            'head_clean': False,
            'remove_line': False,
            'tbl_hdr_done': False,
            'last_ln_empty': False,
            'last_label_removed': False,
            'con_empty_ln_cnt': 0,
            'in_stat_tbl': 0,
            'in_log_blk': 0,
            'last_label': '',
            'curr_line_ts': ''
        }

        print(f"Pre-processing the raw {self.datatype} dataset ...")
        parse_st: datetime = datetime.now()

        #
        # A low overhead progress bar
        # https://github.com/tqdm/tqdm#documentation
        # If only display statics w/o bar, set ncols=0
        #
        pbar = tqdm(total=len(self._rawlogs), unit='Lines', disable=False,
                    bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

        for idx, line in enumerate(self._rawlogs):
            # Update the progress bar
            pbar.update(1)

            # ----------------------------------------------------------
            # Handle the main timestamp
            # ----------------------------------------------------------

            # Save the main timestamp if it exists. The newline does not
            # have the main timestamp before write it back to new file.
            # The train label and the session label are also considered.
            # Add them back along with the main timestamp at the end.
            match_ts = self.ptn_main_ts.match(line)
            if self._reserve_ts and match_ts:
                # Strip the main timestamp including train and session
                # labels if any exist
                stat['curr_line_ts'] = match_ts.group(0)
                if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                    and not (self.training or self.metrics) \
                    and not ptn.PTN_FUZZY_TIME.search(stat['curr_line_ts']):
                    if idx == 0:
                        stat['head_clean'] = True
                    continue
                newline = self.ptn_main_ts.sub('', line, count=1)
                # Inherit segment labels (segsign: or cxxx) from last
                # labeled line if it is removed.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics) \
                    and stat['last_label_removed']:
                    stat['curr_line_ts'] = ''.join([stat['curr_line_ts'], stat['last_label']])
                    # Reset
                    stat['last_label_removed'] = False
                    stat['last_label'] = ''
            elif self._reserve_ts:
                # If we intend to reserve the main timestamp but does
                # not match, delete this line. This usually happens when
                # the timestamp is messed up, the timestamp format is
                # not recognized, or no timestamp at all at the head.
                if idx == 0:
                    stat['head_clean'] = True
                continue
            else:
                # No main timestamp in the log file or we do not want to
                # reserve it
                newline = line

            # ----------------------------------------------------------
            # No main timestamp and train label since then until adding
            # them back at the end of preprocess_new.
            # ----------------------------------------------------------

            #
            # Remove some heading lines at the start of log file
            #
            if (idx == 0 or stat['head_clean']) \
                and (ptn.PTN_NESTED_LINE.match(newline) or newline in ['\n', '\r\n']):
                stat['head_clean'] = True
                # Take care if the removed line has segment label. Hand
                # it over to the next line.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    stat['last_label'], stat['last_label_removed'] \
                        = self._hand_over_label(stat['curr_line_ts'])
                continue
            if stat['head_clean']:
                stat['head_clean'] = False

            #
            # Note:
            # Starting from here, remove one line by using remove_line
            # in state variable instead of 'continue' directly.
            #

            #
            # Line processing for each kind of LOG_TYPE.
            # @abstractmethod: Override it in the derived class
            #
            newline = self.process_for_domain(newline, stat)

            #
            # It is time to remove empty line
            #
            # if newline in ['\n', '\r\n', '']:
            if ptn.PTN_EMPTY_LINE.match(newline):
                if not stat['last_ln_empty']:
                    stat['con_empty_ln_cnt'] = 1
                else:
                    stat['con_empty_ln_cnt'] += 1

                # Take care if the removed line has segment label. Hand
                # it over to the next line
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    stat['last_label'], stat['last_label_removed'] \
                        = self._hand_over_label(stat['curr_line_ts'])

                # Update last_ln_empty for the next line processing
                stat['last_ln_empty'] = True
                stat['remove_line'] = True
            else:
                stat['last_ln_empty'] = False

            #
            # Line removing (including empty) should precede here
            #
            if stat['remove_line']:
                stat['remove_line'] = False
                continue

            #
            # Split some tokens apart
            # @abstractmethod: Override it in the derived class
            #
            newline = self.split_tokens(newline, False)

            # ----------------------------------------------------------
            # Add session label 'segsign: ' for DeepLog.
            # In DeepLog training or validation, use multi-session logs.
            # The metrics means doing validation on test dataset or not.
            # ----------------------------------------------------------
            # @abstractmethod: Override it in the derived class
            #
            if self.context in ['DEEPLOG'] and (self.training or self.metrics):
                if self.match_session_label(newline):
                    newline = ''.join(['segsign: ', newline])

            # ----------------------------------------------------------
            # Add back the timestamp if it exists and store new line
            # ----------------------------------------------------------
            if self._reserve_ts and match_ts:
                newline = ''.join([stat['curr_line_ts'], newline])
            self._newlogs.append(newline)

            # The raw line index list in the new file
            # Do it only for prediction in DeepLog/Loglab and OSS
            if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                and not (self.training or self.metrics):
                self._map_new_raw.append(idx+1)

        pbar.close()

        # Conditionally save the newlogs to a file per the config file
        self.cond_save_strings(self.fzip['new'], self._newlogs)

        print(f"Purge costs {datetime.now()-parse_st}\n")

    # pylint: disable=too-many-branches
    def preprocess_norm(self):
        """
        Preprocess to generate the norm log data.
        Normalize the new log data, aka. converting multi-line log to
        one line.
        \b
        Note:
            Overwrite this func if multi-line log has a different format
            instead of primary/nested combination.
        """
        # Bail out early for the wrong LOG_TYPE
        if self._log_head_offset < 0:
            return

        # Reset normlogs in case it is not empty
        self._normlogs = []

        if not GC.conf['general']['aim']:
            with open(self.fzip['new'], 'r', encoding='utf-8') as newfile:
                self._newlogs = newfile.readlines()

        # Make sure newlogs is not empty. Usually if the preprocess_new
        # thinks the timestamp format is abnormal, it will delete all
        # the lines and leads to an empty newlogs.
        if len(self._newlogs) == 0:
            print("Timestamps are abnormal, or not standard for training!!!")
            sys.exit(1)

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
                last_line = ''.join([last_line.rstrip(), ', ', newline.lstrip()])
            else:
                # If current is primary line, then concatenating ends
                if self._reserve_ts and match_ts and (last_line != ''):
                    last_line = ''.join([last_line_ts, last_line])
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
            last_line = ''.join([last_line_ts, last_line])
        self._normlogs.append(last_line)

        # Conditionally save the normlogs and rawln idx to files
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'w', encoding='utf-8') as fnorm:
                fnorm.writelines(self._normlogs)

            if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                and not (self.training or self.metrics):
                with open(self.fzip['map_norm_raw'], 'wb') as fridx:
                    pickle.dump(self._map_norm_raw, fridx)

    def preprocess(self):
        """
        Preprocess in whole.
        """
        self.preprocess_new()
        self.preprocess_norm()

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
        data/cooked/train.txt or data/cooked/test.txt.
        """
        raw_in_lst: List[str] = []
        self._rawlogs = []

        for fname in file_names:
            raw_in_lst.append(os.path.join(raw_dir, fname))
        for rawf in raw_in_lst:
            with open(rawf, 'r', encoding='utf-8-sig') as rawin:
                self._rawlogs += rawin.readlines()
            # Make sure preceding file has line feed at EOF
            self.add_line_feed(self._rawlogs)

        # Conditionally save the rawlogs to train.txt or test.txt.
        self.cond_save_strings(self.fzip['raw'], self._rawlogs)

    def cat_files_dir(self, raw_dir: str):
        """
        Cat all raw log files under raw_dir (including sub-dirs) into a
        monolith for template gen/update and Loglizer. Monolith file is
        either data/cooked/train.txt or data/cooked/test.txt based on
        the config settings.
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
                # Make sure preceding file has line feed at EOF
                self.add_line_feed(self._rawlogs)

        # Conditionally save the rawlogs to train.txt or test.txt.
        self.cond_save_strings(self.fzip['raw'], self._rawlogs)

    def cat_files_deeplog(self, raw_dir: str):
        """
        Cat all raw log files under raw_dir (including sub-dirs) into a
        a monolith. This is used for DeepLog training and validation by
        considering session labels. Monolith is either the data/cooked/
        train.txt or data/cooked/test.txt based on the config settings.
        """
        self._rawlogs = []

        for dirpath, _, files in sorted(os.walk(raw_dir, topdown=True)):
            # print(f'Found directory: {dirpath}')
            for filename in files:
                if filename in dh.SKIP_FILE_LIST:
                    continue
                self.cat_segment(dirpath, filename, dh.SESSION_LABEL, self._rawlogs)

        # Conditionally save the rawlogs to train.txt or test.txt.
        self.cond_save_strings(self.fzip['raw'], self._rawlogs)

    def cat_files_loglab(self):
        """
        Cat all raw log files under raw_dir (including sub-dirs) into a
        monolith. Extract class names. This is used for Loglab training.
        Monolith is data/train.txt
        """
        self._rawlogs = []

        loglab_dir = os.path.join(dh.RAW_DATA, 'loglab')
        # Note: name the class folder as 'cxxx', and the training log
        # files in it as '*_xxx.txt'. Concatenate the files under dir
        # data/raw/LOG_TYPE/loglab/c001/ ... /cxxx/.
        for dirpath, _, files in sorted(os.walk(loglab_dir, topdown=True)):
            # print(f'Found directory: {dirpath}')
            # Extract class name (sub-folder cxxx, dirpath[-4:])
            classname = re.split(r'[\\|/]', dirpath.strip('[\\|/]'))[-1]
            if not ptn.PTN_CLASS_LABEL.match(classname):
                # Skip loglab itself and non-standard class name sub
                # folders if any exists.
                continue
            # Sort the files per the file name string[-7:-4], aka. the 3
            # digits num part.
            for filename in sorted(files, key=lambda x:x[-7:-4]):
                self.cat_segment(dirpath, filename, ''.join([classname, ' ']), self._rawlogs)

        # Conditionally save the rawlogs to train.txt.
        self.cond_save_strings(self.fzip['raw'], self._rawlogs)

    def cat_segment(self, dpath: str, fname: str, seglabel: str, mono: List[str]):
        """
        Cat files and insert segment labels to mark the original file
        boundary.
        """
        rawf = os.path.join(dpath, fname)
        # print(rawf)
        with open(rawf, 'r', encoding='utf-8-sig') as rawin:
            for idx, line in enumerate(rawin):
                # Insert segment label to the start line of each file
                if idx == 0:
                    match_ts = ptn.PTN_STD_TS.match(line)
                    if match_ts:
                        cur_line_ts = match_ts.group(0)
                        newline = ptn.PTN_STD_TS.sub('', line, count=1)
                        line = ''.join([cur_line_ts, seglabel, newline])
                    else:
                        print("Error: The timestamp is wrong!")
                mono.append(line)
        # Make sure preceding file has line feed at EOF
        self.add_line_feed(mono)

    @staticmethod
    def add_line_feed(strlns: List[str]):
        """
        Add line feed at the end of last string if it has no one.
        """
        if strlns[-1][-1] != '\n':
            strlns[-1] = ''.join([strlns[-1], '\n'])

    @staticmethod
    def cond_save_strings(filepath: str, strings: List[str]):
        """
        Conditionally save strings to file per config file settings.
        """
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(filepath, 'w', encoding='utf-8') as fout:
                fout.writelines(strings)

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

    def exceptions_tmplt(self):
        """
        Do some exceptional prework for template update. Overwrite it if
        you need some works to do in the normal process before template
        update. It is optional.
        """

    @staticmethod
    def split_token_apart(line: str, ptn_left: Pattern[str], ptn_right: Pattern[str]):
        """
        Split some token apart per the regx patterns
        """
        for ptn_obj in ptn_left:
            mtch = ptn_obj.search(line)
            if mtch:
                line = ptn_obj.sub(''.join([mtch.group(0), ' ']), line)

        for ptn_obj in ptn_right:
            mtch = ptn_obj.search(line)
            if mtch:
                line = ptn_obj.sub(''.join([' ', mtch.group(0)]), line)

        return line

    @abstractmethod
    def split_tokens(self, line: str, lite: bool):
        """ Split some token apart per the regx patterns """

    @abstractmethod
    def clean_misc_char(self, line: str):
        """ Clean console prompt, unwanted chars, etc """

    @abstractmethod
    def match_session_label(self, line: str):
        """ Match session label for DeepLog """
