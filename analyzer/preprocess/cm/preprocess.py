# Licensed under the MIT License - see LICENSE.txt
""" Derived class of preprocess. LOG_TYPE specific.
"""
import os
from datetime import datetime
import logging
from typing import List, Dict, Pattern
from tqdm import tqdm
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import PreprocessBase
from . import patterns as ptn


__all__ = ["Preprocess"]

log = logging.getLogger(__name__)


# ---------------------------------------------
# Terminologies:
# primary line - no space proceeded
# nested line  - one or more spaces proceeded
# empty line   - LF or CRLF only in one line
# ---------------------------------------------

class Preprocess(PreprocessBase):
    """ The class of preprocess. """
    def __init__(self):
        PreprocessBase.__init__(self)

    def preprocess_ts(self):
        """ Preprocess before learning timestamp width.
            Only for prediction of (OSS, DeepLog or Loglab)
            Not for Loglizer as it requires timestamps for windowing
        """
        log.info("Preprocess before timestamp detection.")

        # Reset normlogs in case it is not empty
        self._normlogs = []

        for idx, line in enumerate(self._rawlogs):

            # Remove the NULL char '\0' at the first line if it exists
            if idx == 0 and line[0] == '\0':
                continue

            # Remove other timestamps, console prompt and unwanted chars
            line = ptn.PTN_CLEAN_CHAR.sub('', line)

            # Remove empty line
            if line in ['\n', '\r\n']:
                continue

            # Split some tokens apart
            line = self.split_token_apart(line, ptn.PTN_SPLIT_LEFT_TS,
                                          ptn.PTN_SPLIT_RIGHT_TS)

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
        """ Preprocess to generate the new log data.
            Clean the raw log data.
        """
        log.info("Preprocess to generate new log data.")
        # For prediction, the timestamp in the test log is unknown or
        # even does not exist. The preprocess will try to learn the
        # width of the unknown timestamp in advance. So here get the
        # updated info instead of the default one in config file.
        self._get_timestamp_info()

        # Reset newlogs in case it is not empty
        self._newlogs = []

        #-------------------------------
        # Local state variables
        #-------------------------------
        last_label: str = ''
        con_empty_ln_cnt: int = 0

        stat: Dict[str, bool] = {
            'head_clean': False,
            'remove_line': False,
            'in_ds_stat_tbl': False,
            'in_us_stat_tbl': False,
            'tbl_hdr_done': False,
            'last_ln_empty': False,
            'last_label_removed': False,
            'in_log_tbl': False,
            'in_log_blk': False,
            'in_log_blk2': False,
            'in_log_blk3': False,
            'in_log_blk4': False
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
                curr_line_ts = match_ts.group(0)
                if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                    and not (self.training or self.metrics) \
                    and not ptn.PTN_FUZZY_TIME.search(curr_line_ts):
                    if idx == 0:
                        stat['head_clean'] = True
                    continue
                newline = self.ptn_main_ts.sub('', line, count=1)
                # Inherit segment labels (segsign: or cxxx) from last
                # labeled line if it is removed.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics) \
                    and stat['last_label_removed']:
                    curr_line_ts = ''.join([curr_line_ts, last_label])
                    # Reset
                    stat['last_label_removed'] = False
                    last_label = ''
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
                    last_label, stat['last_label_removed'] \
                        = self._hand_over_label(curr_line_ts)
                continue
            if stat['head_clean']:
                stat['head_clean'] = False

            # Because of host system code bug of no endl, some primary
            # logs are concatenated to the former one. Split them and
            # only reserve the last log in the same line. Skip the match
            # at position 0 if exits as we will remove it later. Also
            # exclude the case that tables are involved.
            if ptn.PTN_BFC_TS.search(newline, 2) \
                and not ptn.PTN_NESTED_LINE.match(newline) \
                and not ptn.PTN_TABLE_TITLE_COMMON.match(newline):
                #
                match_g = ptn.PTN_BFC_TS.finditer(newline, 2)
                *_, last_match = match_g
                newline = newline[last_match.start() :]

            #
            # Note:
            # Starting from here, remove one line by using remove_line
            # instead of 'continue' directly.
            #

            #
            # Remove other timestamps, console prompt and unwanted chars
            #
            newline = ptn.PTN_CLEAN_CHAR.sub('', newline)

            #
            # Remove unwanted log blocks. Specific lines end the block
            #
            if ptn.PTN_BLOCK_RM_START.match(newline):
                stat['in_log_blk'] = True
                # Delete current line
                stat['remove_line'] = True
            elif stat['in_log_blk']:
                if ptn.PTN_BLOCK_RM_END.match(newline):
                    stat['in_log_blk'] = False
                else:
                    # Delete current line
                    stat['remove_line'] = True

            #
            # Remove unwanted log blocks. Primary line ends the block
            #
            elif ptn.PTN_BLOCK_RM_PRI.match(newline):
                stat['in_log_blk2'] = True
                # Delete current line
                stat['remove_line'] = True
            elif stat['in_log_blk2']:
                if not ptn.PTN_NESTED_LINE.match(newline) and newline not in ['\n', '\r\n']:
                    stat['in_log_blk2'] = False
                else:
                    # Delete current line
                    stat['remove_line'] = True

            #
            # Remove line starting with specific patterns
            #
            elif ptn.PTN_LINE_RM.match(newline):
                # Take care if the removed line has segment label. Hand
                # it over to the next line.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    last_label, stat['last_label_removed'] \
                        = self._hand_over_label(curr_line_ts)
                stat['remove_line'] = True

            #
            # Indent a block of lines from primary to embedded. Note:
            # Do not indent the first line. Empty line ends the block.
            #
            elif ptn.PTN_BLOCK_INDENT.match(newline):
                stat['in_log_blk3'] = True
            elif stat['in_log_blk3']:
                # Empty line ends the block
                if newline in ['\n', '\r\n']:
                    stat['in_log_blk3'] = False
                else:
                    newline = ''.join([' ', newline])

            #
            # Indent a block of lines from primary to embedded. Note:
            # Do not indent the first line. Special line (inclusive)
            # ends the block.
            #
            elif ptn.PTN_BLOCK_INDENT2.match(newline):
                stat['in_log_blk4'] = True
            elif stat['in_log_blk4']:
                if ptn.PTN_BLOCK_INDENT2_END.match(newline):
                    # Special line ends the block
                    newline = ''.join([' ', newline])
                    stat['in_log_blk4'] = False
                else:
                    newline = ''.join([' ', newline])

            #
            # Indent some specific lines
            #
            elif ptn.PTN_PRI_TO_NESTED.match(newline):
                # Indent this line
                newline = ''.join([' ', newline])

            #
            # Format DS channel status table
            #
            elif ptn.PTN_DS_CHAN_TABLE_START.match(newline):
                stat['in_ds_stat_tbl'] = True
                # Remove the title line
                stat['remove_line'] = True
            elif stat['in_ds_stat_tbl']:
                newline, \
                stat['in_ds_stat_tbl'], \
                stat['tbl_hdr_done'], \
                stat['remove_line'] \
                    = self.format_chan_stat_table(
                    newline, stat['in_ds_stat_tbl'], stat['tbl_hdr_done'],
                    stat['remove_line'], ptn.PTN_DS_CHAN_TABLE_END.match(newline), 'DS'
                )

            #
            # Format US channel status table
            #
            elif ptn.PTN_US_CHAN_TABLE_START.match(newline):
                stat['in_us_stat_tbl'] = True
                # Remove the title line
                stat['remove_line'] = True
            elif stat['in_us_stat_tbl']:
                newline, \
                stat['in_us_stat_tbl'], \
                stat['tbl_hdr_done'], \
                stat['remove_line'] \
                    = self.format_chan_stat_table(
                    newline, stat['in_us_stat_tbl'], stat['tbl_hdr_done'],
                    stat['remove_line'], ptn.PTN_US_CHAN_TABLE_END.match(newline), 'US'
                )

            #
            # Remove other tables. Should be behind DS/Us chan tables.
            #
            elif ptn.PTN_TABLE_TITLE_COMMON.match(newline):
                stat['in_log_tbl'] = True
                # Remove the title line
                stat['remove_line'] = True
            elif stat['in_log_tbl']:
                if newline in ['\n', '\r\n']:
                    # Suppose table ended with empty line
                    stat['in_log_tbl'] = False
                else:
                    # Still table line, remove it
                    stat['remove_line'] = True

            #
            # Remove title line of specific tables
            #
            elif ptn.PTN_TABLE_TITLE.match(newline):
                stat['remove_line'] = True

            #
            # Convert some specific nested lines as primary
            #
            elif ptn.PTN_NESTED_TO_PRI.match(newline):
                newline = newline.lstrip()

            #
            # Convert nested as primary if two more empty lines procede
            #
            elif ptn.PTN_NESTED_LINE.match(newline) and stat['last_ln_empty'] \
                and (con_empty_ln_cnt>=2):
                # Try to see if there are any exceptions
                if not ptn.PTN_NESTED_LINE_EXCEPTION.match(newline):
                    newline = newline.lstrip()

            #
            # It is time to remove empty line
            #
            if newline in ['\n', '\r\n', '']:
                if not stat['last_ln_empty']:
                    con_empty_ln_cnt = 1
                else:
                    con_empty_ln_cnt += 1

                # Take care if the removed line has segment label. Hand
                # it over to the next line
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    last_label, stat['last_label_removed'] \
                        = self._hand_over_label(curr_line_ts)

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
            #
            newline = self.split_token_apart(newline, ptn.PTN_SPLIT_LEFT,
                                             ptn.PTN_SPLIT_RIGHT)

            # ----------------------------------------------------------
            # Add session label 'segsign: ' for DeepLog.
            # In DeepLog training or validation, use multi-session logs.
            # metrics means doing validation on test dataset or not.
            # ----------------------------------------------------------
            if self.context in ['DEEPLOG'] and (self.training or self.metrics):
                if ptn.PTN_SESSION.match(newline):
                    newline = ''.join(['segsign: ', newline])

            # ----------------------------------------------------------
            # Add back the timestamp if it exists and store new line
            # ----------------------------------------------------------
            if self._reserve_ts and match_ts:
                newline = ''.join([curr_line_ts, newline])
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

    # pylint: disable=too-many-arguments
    def format_chan_stat_table(self, line: str, in_ch_stat_tbl: bool, tbl_hdr_done: bool,
                               remove_line: bool, is_table_end: bool, chan: str):
        """ Common entry for ds/us channel status table formating """
        if is_table_end:
            # End the table with specific line and reset states
            in_ch_stat_tbl = False
            tbl_hdr_done = False
        elif (not ptn.PTN_NESTED_LINE.match(line)) and (line not in ['\n', '\r\n']):
            # Table is messed by other thread if gets into here. Normal
            # channel status row should be nested. This line comes from
            # another thread. Remove or keep it?
            # remove_line = True
            pass
        elif ptn.PTN_TABLE_TITLE_COMMON.match(line):
            # End the table header and remove the common title
            tbl_hdr_done = True
            remove_line = True
        elif not tbl_hdr_done:
            # Remove the line (including empty) in table header
            remove_line = True
        elif line not in ['\n', '\r\n']:
            # Format the table contents now
            if chan == 'DS':
                line, remove_line = self.format_ds_chan_table(line, remove_line)
            else:
                line, remove_line = self.format_us_chan_table(line, remove_line)

        return line, in_ch_stat_tbl, tbl_hdr_done, remove_line

    def format_ds_chan_table(self, line: str, remove_line: bool):
        """ Format one item of ds channel table """
        # ---raw table---
        # Active Downstream Channel Diagnostics:
        #
        #   rx id  dcid    freq, hz  qam  fec   snr, dB   power, dBmV  modulation
        #                            plc  prfA
        #   -----  ----  ----------  ---  ---  ---------  -----------  ----------
        #       0*    1   300000000   y    y          35            3       Qam64
        #       1     2   308000000   y    y          34            4      Qam256
        #      32    66   698000000   y    y          35            1    OFDM PLC
        #

        # ---one item after cooking---
        # DS channel status, rxid 0, dcid 1, freq 300000000, qam y,
        # fec y, snr 35, power 3, mod Qam256
        lineview: List[str] = line.split(None, 7)

        # Make sure the line has right num of tokens. If it has smaller
        # num, the line either is from another thread or some of tokens
        # at the begining of this line are eaten by console prompt.
        try:
            _ = lineview[7]
        except IndexError:
            # Bail out early and remove this line
            remove_line = True
            return line, remove_line

        # The last column of current line might be concatednated by
        # other thread outputs inadvertently.
        if lineview[7] not in ['Qam64\n', 'Qam256\n', 'OFDM PLC\n', 'Unknown\n',
            'Qam64\r\n', 'Qam256\r\n', 'OFDM PLC\r\n', 'Unknown\r\n']:
            if lineview[7][3] == '6':
                lineview[7] = 'Qam64\n'
            elif lineview[7][3] == '2':
                lineview[7] = 'Qam256\n'
            elif lineview[7][0] == 'O':
                lineview[7] = 'OFDM PLC\n'
            elif lineview[7][0] == 'U':
                lineview[7] = 'Unknown\n'
            else:
                # Current line is severely broken, or it is a nested
                # line from another thread. Unrecoverable, remove it.
                # Bail out early and remove this line
                remove_line = True
                return line, remove_line

        if lineview[7][0] == 'O':
            # Keep OFDM channel status log length as same as QAM channel
            # Then they will share same log template after clustering.
            lineview[7] = 'OFDM_PLC\n'

        line = ''.join(self.ds_chan_log(lineview))
        return line, remove_line

    @staticmethod
    def ds_chan_log(lineview: List[str]):
        """ New format for downstream channel table """
        yield 'DS channel status rxid '
        yield lineview[0]
        yield ' dcid '
        yield lineview[1]
        yield ' freq '
        yield lineview[2]
        yield ' qam '
        yield lineview[3]
        yield ' fec '
        yield lineview[4]
        yield ' snr '
        yield lineview[5]
        yield ' power '
        yield lineview[6]
        yield ' mod '
        yield lineview[7]

    def format_us_chan_table(self, line: str, remove_line: bool):
        """ Format one item of us channel table """
        # ---raw table---
        # Active Upstream Channels:
        #
        #                     rng     pwr        frequency     symbols   phy  ok tx
        #  txid  ucid  dcid   sid     dBmv          MHz          sec    type  data?
        #  ----  ----  ----  ------  -----    ---------------  -------  ----  -----
        #     0   101     1     0x2      18             9.000  5120000     3      y
        #     1   102     1     0x2      18            15.400  5120000     3      y
        #     8   149     1     0x2      18   63.700 - 78.450        0     5      y
        #

        # ---one item after cooking---
        # US channel status, txid 0, ucid 101, dcid 1, rngsid 0x2,
        # power 18, freq_start 9.000, freq_end 9.000, symrate 5120000,
        # phytype 3, txdata y
        lineview: List[str] = line.split(None, 8)

        # Make sure the line has right num of tokens
        try:
            _ = lineview[8]
        except IndexError:
            # Bail out early and remove this line
            remove_line = True
            return line, remove_line

        if lineview[6] == '-':
            # This line is for OFDMA channel, split it again
            lineview = line.split(None, 10)

            # Make sure the line has right num of tokens
            try:
                _ = lineview[10]
            except IndexError:
                # Bail out early and remove this line
                remove_line = True
                return line, remove_line

            line = ''.join(self.us_chan_log_ofdma(lineview))
        else:
            # For SC-QAM channels
            line = ''.join(self.us_chan_log_scqam(lineview))
        return line, remove_line

    @staticmethod
    def us_chan_log_ofdma(lineview: List[str]):
        """ New format for upstream ofdma channel table """
        yield 'US channel status txid '
        yield lineview[0]
        yield ' ucid '
        yield lineview[1]
        yield ' dcid '
        yield lineview[2]
        yield ' rngsid '
        yield lineview[3]
        yield ' power '
        yield lineview[4]
        yield ' freqstart '
        yield lineview[5]
        yield ' freqend '
        yield lineview[7]
        yield ' symrate '
        yield lineview[8]
        yield ' phytype '
        yield lineview[9]
        yield ' txdata '
        yield lineview[10]

    @staticmethod
    def us_chan_log_scqam(lineview: List[str]):
        """ New format for upstream scqam channel table """
        yield 'US channel status txid '
        yield lineview[0]
        yield ' ucid '
        yield lineview[1]
        yield ' dcid '
        yield lineview[2]
        yield ' rngsid '
        yield lineview[3]
        yield ' power '
        yield lineview[4]
        yield ' freqstart '
        yield lineview[5]
        yield ' freqend '
        yield lineview[5]
        yield ' symrate '
        yield lineview[6]
        yield ' phytype '
        yield lineview[7]
        yield ' txdata '
        yield lineview[8]

    @staticmethod
    def split_token_apart(line: str, ptn_left: Pattern[str], ptn_right: Pattern[str]):
        """ Split some token apart per the regx patterns """
        for ptn_obj in ptn_left:
            mtch = ptn_obj.search(line)
            if mtch:
                line = ptn_obj.sub(''.join([mtch.group(0), ' ']), line)

        for ptn_obj in ptn_right:
            mtch = ptn_obj.search(line)
            if mtch:
                line = ptn_obj.sub(''.join([' ', mtch.group(0)]), line)

        return line

    def exceptions_tmplt(self):
        """ Do some exceptional works of template update """
        # Insert data/raw/cm/others/temp_updt_manu.txt to the head of
        # data/cooked/cm/train.txt when doing template lib gen/update.
        # This workarounds some similarity threshold issue in Drain
        # agorithm. Unix cat however will generate trailing ^M char.
        src1 = os.path.join(dh.RAW_DATA, 'others', 'temp_updt_manu.txt')

        rawlogs: List[str] = []
        with open(src1, 'r', encoding='utf-8-sig') as rawfile:
            rawlogs = rawfile.readlines()
        # Make sure preceding file has line feed at EOF
        self.add_line_feed(rawlogs)

        self._rawlogs = rawlogs + self._rawlogs

        # Conditionally save the rawlogs to file per config.
        self.cond_save_strings(self.fzip['raw'], self._rawlogs)
