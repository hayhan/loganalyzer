# Licensed under the MIT License - see License.txt
""" Derived class of preprocess. LOG_TYPE specific.
"""
import os
import sys
from shutil import copyfile
from datetime import datetime
import logging
from typing import List, Pattern
from tqdm import tqdm
import analyzer.utils.data_helper as dh
from analyzer.config import GlobalConfig as GC
from analyzer.preprocess import PreprocessBase
from . import patterns as ptn


__all__ = [
    "Preprocess",
]

# ---------------------------------------------
# Terminologies:
# primary line - no space proceeded
# nested line  - one or more spaces proceeded
# empty line   - LF or CRLF only in one line
# ---------------------------------------------

log = logging.getLogger(__name__)

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
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['norm'], 'w', encoding='utf-8') as fnorm:
                fnorm.writelines(self._normlogs)


    # pylint: disable=too-many-locals；too-many-statements
    # pylint: disable=too-many-branches
    def preprocess_new(self):
        """ Preprocess to generate the new log data.
            Clean the raw log data.
        """
        log.info("Preprocess to generate new log data.")
        # For prediction, the timestamp in the test log is unknown or
        # even does not exist. The preprocess will try to learn the
        # width of the unknown timestamp in advance. So here get the
        # updated info instead of the default one in cofig file.
        self._get_timestamp_info()

        # Reset newlogs in case it is not empty
        self._newlogs = []

        #-------------------------------
        # Local state variables
        #-------------------------------
        heading_clean: bool = False
        remove_line: bool = False
        in_ds_stat_table: bool = False
        in_us_stat_table: bool = False
        table_messed: bool = False
        table_entry_processed: bool = False
        last_ln_messed: bool = False
        in_log_table: bool = False
        in_log_block: bool = False
        in_log_block2: bool = False
        in_log_block3: bool = False
        in_log_block4: bool = False
        last_line_empty: bool = False
        con_empty_ln_cnt: int = 0
        last_label_removed: bool = False
        last_label: str = ''

        print("Pre-processing the raw {0} dataset ...".format(self.datatype))
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
                        heading_clean = True
                    continue
                newline = self.ptn_main_ts.sub('', line, count=1)
                # Inherit segment labels (segsign: or cxxx) from last
                # labeled line if it is removed.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics) \
                    and last_label_removed:
                    curr_line_ts += last_label
                    # Reset
                    last_label_removed = False
                    last_label = ''
            elif self._reserve_ts:
                # If we intend to reserve the main timestamp but does
                # not match, delete this line. This usually happens when
                # the timestamp is messed up, the timestamp format is
                # not recognized, or no timestamp at all at the head.
                if idx == 0:
                    heading_clean = True
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
            if (idx == 0 or heading_clean) \
                and (ptn.PTN_NESTED_LINE.match(newline) or newline in ['\n', '\r\n']):
                heading_clean = True
                # Take care if the removed line has segment label. Hand
                # it over to the next line.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    last_label, last_label_removed = self._hand_over_label(curr_line_ts)
                continue
            if heading_clean:
                heading_clean = False

            # Because of host system code bug of no endl, some primary
            # logs are concatenated to the former one. Split them and
            # only reserve the last log in the same line. Skip the match
            # at position 0 if exits as I will remove it later.
            if ptn.PTN_BFC_TS.search(newline, 2):
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
                in_log_block = True
                # Delete current line
                remove_line = True
            elif in_log_block:
                if ptn.PTN_BLOCK_RM_END.match(newline):
                    in_log_block = False
                else:
                    # Delete current line
                    remove_line = True

            #
            # Remove unwanted log blocks. Primary line ends the block
            #
            elif ptn.PTN_BLOCK_RM_PRI.match(newline):
                in_log_block2 = True
                # Delete current line
                remove_line = True
            elif in_log_block2:
                if not ptn.PTN_NESTED_LINE.match(newline) and newline not in ['\n', '\r\n']:
                    in_log_block2 = False
                else:
                    # Delete current line
                    remove_line = True

            #
            # Remove line starting with specific patterns
            #
            elif ptn.PTN_LINE_RM.match(newline):
                # Take care if the removed line has segment label. Hand
                # it over to the next line.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    last_label, last_label_removed = self._hand_over_label(curr_line_ts)
                remove_line = True

            #
            # Indent a block of lines from primary to embedded. Note:
            # Do not indent the first line. Empty line ends the block.
            #
            elif ptn.PTN_BLOCK_INDENT.match(newline):
                in_log_block3 = True
            elif in_log_block3:
                # Empty line ends the block
                if newline in ['\n', '\r\n']:
                    in_log_block3 = False
                else:
                    newline = ' ' + newline

            #
            # Indent a block of lines from primary to embedded. Note:
            # Do not indent the first line. Special line (inclusive)
            # ends the block.
            #
            elif ptn.PTN_BLOCK_INDENT2.match(newline):
                in_log_block4 = True
            elif in_log_block4:
                if ptn.PTN_BLOCK_INDENT2_END.match(newline):
                    # Special line ends the block
                    newline = ' ' + newline
                    in_log_block4 = False
                else:
                    newline = ' ' + newline

            #
            # Indent some specific lines
            #
            elif ptn.PTN_PRI_TO_NESTED.match(newline):
                # Indent this line
                newline = ' ' + newline

            #
            # Format DS channel status table
            #
            elif ptn.PTN_DS_CHAN_TABLE.match(newline):
                in_ds_stat_table = True
                # Remove the title line
                remove_line = True
            elif in_ds_stat_table and in_log_table:
                if (not ptn.PTN_NESTED_LINE.match(newline)) and (newline not in ['\n', '\r\n']):
                    # Table is messed by other thread if gets into here.
                    # Normal channel status row should be nested. Messed
                    # table may have empty lines in the middle of table.
                    table_messed = True
                    # Remove this line here, do not leave it to the
                    # "Remove table block"
                    remove_line = True
                elif newline in ['\n', '\r\n'] and table_entry_processed and (not last_ln_messed):
                    # Suppose table ended with empty line but also need
                    # consider the case of messed table.
                    # The 'table_entry_processed', 'last_ln_messed' and
                    # 'table_messed' are used here to process the messed
                    # table case. Leave reset of 'in_log_table' to the
                    # "Remove table block".
                    in_ds_stat_table = False
                    table_messed = False
                    table_entry_processed = False
                elif newline not in ['\n', '\r\n']:
                    # The real table row, that is, nested line
                    table_entry_processed = True
                    newline, last_ln_messed \
                        = self.format_ds_chan_table(newline, table_messed, last_ln_messed)

            #
            # Format US channel status table
            #
            elif ptn.PTN_US_CHAN_TABLE.match(newline):
                in_us_stat_table = True
                # Remove the title line
                remove_line = True
            elif in_us_stat_table and in_log_table:
                if newline in ['\n', '\r\n']:
                    # Suppose table ended with empty line. Leave reset
                    # of in_log_table to "remove table block".
                    in_us_stat_table = False
                else:
                    newline = self.format_us_chan_table(newline)

            #
            # Remove table block
            #
            if ptn.PTN_TABLE_TITLE_COMMON.match(newline):
                in_log_table = True
                # Remove the title line
                remove_line = True
            elif in_log_table:
                if newline in ['\n', '\r\n']:
                    # Suppose table ended with empty line
                    # Note: we also reset the in_log_table for the DS/US
                    # channel status table above
                    if (not in_ds_stat_table) or (in_ds_stat_table and \
                        table_entry_processed and (not last_ln_messed)):
                        in_log_table = False
                elif not (in_ds_stat_table or in_us_stat_table):
                    # Still table line, remove it
                    remove_line = True

            #
            # Remove title line of specific tables
            #
            elif ptn.PTN_TABLE_TITLE.match(newline):
                remove_line = True

            #
            # Convert some specific nested lines as primary
            #
            elif ptn.PTN_NESTED_TO_PRI.match(newline):
                newline = newline.lstrip()

            #
            # Convert a nested line as primary if two more empty lines
            # procede.
            #
            elif ptn.PTN_NESTED_LINE.match(newline) and last_line_empty and (con_empty_ln_cnt>=2):
                # Try to see if there are any exceptions
                if not ptn.PTN_NESTED_LINE_EXCEPTION.match(newline):
                    newline = newline.lstrip()

            #
            # It is time to remove empty line
            #
            if newline in ['\n', '\r\n']:
                if not last_line_empty:
                    con_empty_ln_cnt = 1
                else:
                    con_empty_ln_cnt += 1

                # Take care if the removed line has segment label. Hand
                # it over to the next line
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    last_label, last_label_removed = self._hand_over_label(curr_line_ts)

                # Update last_line_empty for the next line processing
                last_line_empty = True
                remove_line = True
            else:
                last_line_empty = False

            #
            # Line removing (including empty) should precede here
            #
            if remove_line:
                remove_line = False
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
                    newline = 'segsign: ' + newline

            # ----------------------------------------------------------
            # Add back the timestamp if it exists and store new line
            # ----------------------------------------------------------
            if self._reserve_ts and match_ts:
                newline = curr_line_ts + newline
            self._newlogs.append(newline)

            # The raw line index list in the new file
            # Do it only for prediction in DeepLog/Loglab and OSS
            if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                and not (self.training or self.metrics):
                self._map_new_raw.append(idx+1)

        pbar.close()

        # Conditionally save the newlogs to a file per the config file
        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['new'], 'w', encoding='utf-8') as fnew:
                fnew.writelines(self._newlogs)

        print('Purge costs {!s}\n'.format(datetime.now()-parse_st))


    @staticmethod
    def format_ds_chan_table(newline: str, table_messed: bool, last_ln_messed: bool):
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
        lineview: List[str] = newline.split(None, 7)
        if table_messed:
            # Need consider the last colomn of DS channel status,
            # aka. lineview[7]
            if lineview[7] not in ['Qam64\n', 'Qam256\n', 'OFDM PLC\n', 'Qam64\r\n', \
                'Qam256\r\n', 'OFDM PLC\r\n']:
                # Current line is messed and the last colomn might be
                # concatednated by other thread printings inadvertently
                # and the next line will be empty. Update last_ln_messed
                # for next line processing.
                last_ln_messed = True
                if lineview[7][3] == '6':           # Qam64
                    lineview[7] = 'Qam64\n'
                elif lineview[7][3] == '2':         # Q256
                    lineview[7] = 'Qam256\n'
                else:
                    lineview[7] = 'OFDM PLC\n'      # OFDM PLC
            else:
                last_ln_messed = False

        if lineview[7][0] == 'O':
            # Keep OFDM channel status log length as same as QAM channel
            # Then they will share same log template after clustering.
            lineview[7] = 'OFDM_PLC\n'              # OFDM PLC

        newline = 'DS channel status' + ' rxid ' + lineview[0] + ' dcid ' + \
                    lineview[1] + ' freq ' + lineview[2] + ' qam ' + \
                    lineview[3] + ' fec ' + lineview[4] + ' snr ' + \
                    lineview[5] + ' power ' + lineview[6] + ' mod ' + lineview[7]
        return newline, last_ln_messed


    @staticmethod
    def format_us_chan_table(newline: str):
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
        lineview: List[str] = newline.split(None, 8)
        if lineview[6] == '-':
            # This line is for OFDMA channel, split it again
            lineview = newline.split(None, 10)
            newline = 'US channel status' + ' txid ' + lineview[0] + ' ucid ' + \
                        lineview[1] + ' dcid ' + lineview[2] + ' rngsid ' + \
                        lineview[3] + ' power ' + lineview[4] + ' freqstart ' + \
                        lineview[5] + ' freqend ' +lineview[7] + ' symrate ' + \
                        lineview[8] + ' phytype ' + lineview[9] + ' txdata ' + \
                        lineview[10]
        else:
            # For SC-QAM channels
            newline = 'US channel status' + ' txid ' + lineview[0] + ' ucid ' + \
                        lineview[1] + ' dcid ' + lineview[2] + ' rngsid ' + \
                        lineview[3] + ' power ' + lineview[4] + ' freqstart ' + \
                        lineview[5] + ' freqend ' +lineview[5] + ' symrate ' + \
                        lineview[6] + ' phytype ' + lineview[7] + ' txdata ' + \
                        lineview[8]
        return newline


    @staticmethod
    def split_token_apart(newline: str, ptn_left: Pattern[str], ptn_right: Pattern[str]):
        """ Split some token apart per the regx patterns """
        for ptn_obj in ptn_left:
            mtch = ptn_obj.search(newline)
            if mtch:
                newline = ptn_obj.sub(mtch.group(0)+' ', newline)

        for ptn_obj in ptn_right:
            mtch = ptn_obj.search(newline)
            if mtch:
                newline = ptn_obj.sub(' '+mtch.group(0), newline)

        return newline

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
        # Add newline in case no one at the end of the heading file
        rawlogs.append('\n')

        self._rawlogs = rawlogs + self._rawlogs

        if GC.conf['general']['intmdt'] or not GC.conf['general']['aim']:
            with open(self.fzip['raw'], 'w', encoding='utf-8') as monolith:
                monolith.writelines(self._rawlogs)
