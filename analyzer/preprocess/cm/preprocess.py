# Licensed under the MIT License - see License.txt
""" Derived class of preprocess.
"""
from datetime import datetime
import logging
from typing import List
from tqdm import tqdm
from analyzer.preprocess.preprocess_base import PreprocessBase
from . import patterns as ptn


__all__ = [
    "Preprocess",
]

# ---------------------------------------------
# Terminology:
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

    # pylint: disable=too-many-locals；too-many-statements;
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

        #-------------------------------
        # Local state variables
        #-------------------------------
        heading_clean: bool = False
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
        # Raw log usually comes from serial console tools like SecureCRT
        # and probably the text file encoding is utf-8 (with BOM). See
        # https://en.wikipedia.org/wiki/Byte_order_mark#UTF-8
        #
        # To skip the BOM when decoding the file, use utf-8-sig codec.
        # https://docs.python.org/3/library/codecs.html
        #
        with open(self.fzip['raw'], 'r', encoding='utf-8-sig') as rawfile:
            rawlines: List[str] = rawfile.readlines()
        rawsize: int = len(rawlines)

        #
        # A low overhead progress bar
        # https://github.com/tqdm/tqdm#documentation
        # If only display statics w/o bar, set ncols=0
        #
        pbar = tqdm(total=rawsize, unit='Lines', disable=False,
                    bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

        for idx, line in enumerate(rawlines):
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
            # No main timestamp and train label since then before adding
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
                    label_match = ptn.PTN_LABEL.search(curr_line_ts)
                    if label_match:
                        last_label = label_match.group(0)
                        last_label_removed = True
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
            # Remove other timestamps, console prompt and unwanted chars
            #
            newline = ptn.PTN_CLEAN_CHAR.sub('', newline)

            #
            # Remove unwanted log blocks. Specific lines end the block
            #
            if ptn.PTN_BLOCK_RM_START.match(newline):
                in_log_block = True
                # Delete current line
                # Update for the next line
                last_line_empty = False
                continue
            if in_log_block:
                if ptn.PTN_BLOCK_RM_END.match(newline):
                    in_log_block = False
                else:
                    # Delete current line
                    # Update for the next line
                    last_line_empty = False
                    continue

            #
            # Remove unwanted log blocks. Primary line ends the block
            #
            if ptn.PTN_BLOCK_RM_PRI.match(newline):
                in_log_block2 = True
                # Delete current line
                # Update for the next line
                last_line_empty = False
                continue
            if in_log_block2:
                if not ptn.PTN_NESTED_LINE.match(newline) and newline not in ['\n', '\r\n']:
                    in_log_block2 = False
                else:
                    # Delete current line
                    # Update for the next line
                    last_line_empty = False
                    continue

            #
            # Remove line starting with specific patterns
            #
            if ptn.PTN_LINE_RM.match(newline):
                # Take care if the removed line has segment label. Hand
                # it over to the next line.
                if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                    label_match = ptn.PTN_LABEL.search(curr_line_ts)
                    if label_match:
                        last_label = label_match.group(0)
                        last_label_removed = True
                # Update for the next line
                last_line_empty = False
                continue

            # Format DS channel status table
            #
            # Active Downstream Channel Diagnostics:
            #
            #   rx id  dcid    freq, hz  qam  fec   snr, dB   power, dBmV  modulation
            #                            plc  prfA
            #   -----  ----  ----------  ---  ---  ---------  -----------  ----------
            #       0*    1   300000000   y    y          35            3       Qam64
            #       1     2   308000000   y    y          34            4      Qam256
            #      32    66   698000000   y    y          35            1    OFDM PLC
            #
            if ptn.PTN_DS_CHAN_TABLE.match(newline):
                in_ds_stat_table = True
            elif in_ds_stat_table and in_log_table:
                if (not ptn.PTN_NESTED_LINE.match(newline)) and (newline not in ['\n', '\r\n']):
                    # The table is messed by printings from other thread
                    # if we run into here. The normal DS channel status
                    # row should be nested by default. The messed table
                    # might have empty lines in the middle of table.
                    table_messed = True
                    # Remove this line here, do not leave it to the
                    # "Remove table block"
                    # Update for the next line
                    last_line_empty = False
                    continue
                if newline in ['\n', '\r\n'] and table_entry_processed and (not last_ln_messed):
                    # Suppose table ended with empty line but need also
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
                    # ---Convert current line to new ds format---
                    # DS channel status, rxid 0, dcid 1, freq 300000000,
                    # qam y, fec y, snr 35, power 3, mod Qam256
                    lineview = newline.split(None, 7)
                    if table_messed:
                        # Need consider the last colomn of DS channel
                        # status, aka. lineview[7]
                        if lineview[7] not in ['Qam64\n', 'Qam256\n', 'OFDM PLC\n', 'Qam64\r\n', \
                            'Qam256\r\n', 'OFDM PLC\r\n']:
                            # Current line is messed and the last colomn
                            # might be concatednated by other thread
                            # printings inadvertently and the next line
                            # will be empty. Update last_ln_messed for
                            # next line processing.
                            last_ln_messed = True
                            if lineview[7][3] == '6':       # Qam64
                                lineview[7] = 'Qam64\n'
                            elif lineview[7][3] == '2':     # Q256
                                lineview[7] = 'Qam256\n'
                            else:
                                lineview[7] = 'OFDM PLC\n'  # OFDM PLC
                        else:
                            last_ln_messed = False

                    if lineview[7][0] == 'O':
                        # Keep the OFDM channel status log length as
                        # same as QAM channel. Then they will share the
                        # same log template after clustering.
                        lineview[7] = 'OFDM_PLC\n'          # OFDM PLC

                    newline = 'DS channel status' + ' rxid ' + lineview[0] + ' dcid ' + \
                              lineview[1] + ' freq ' + lineview[2] + ' qam ' + lineview[3] + \
                              ' fec ' + lineview[4] + ' snr ' + lineview[5] + ' power ' + \
                              lineview[6] + ' mod ' + lineview[7]

            # Format US channel status table
            #
            # Active Upstream Channels:
            #
            #                     rng     pwr        frequency     symbols   phy  ok tx
            #  txid  ucid  dcid   sid     dBmv          MHz          sec    type  data?
            #  ----  ----  ----  ------  -----    ---------------  -------  ----  -----
            #     0   101     1     0x2      18             9.000  5120000     3      y
            #     1   102     1     0x2      18            15.400  5120000     3      y
            #     8   149     1     0x2      18   63.700 - 78.450        0     5      y
            #
            if ptn.PTN_US_CHAN_TABLE.match(newline):
                in_us_stat_table = True
            elif in_us_stat_table and in_log_table:
                if newline in ['\n', '\r\n']:
                    # Suppose table ended with empty line. Leave reset
                    # of in_log_table to "remove table block".
                    in_us_stat_table = False
                else:
                    # ---Convert current line to new us format---
                    # US channel status, txid 0, ucid 101, dcid 1,
                    # rngsid 0x2, power 18, freq_start 9.000,
                    # freq_end 9.000, symrate 5120000, phytype 3,
                    # txdata y
                    lineview = newline.split(None, 8)
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

            #
            # Remove table block
            #
            if ptn.PTN_TABLE_TITLE_COMMON.match(newline):
                in_log_table = True
                # Update for the next line
                last_line_empty = False
                continue
            if in_log_table:
                if newline in ['\n', '\r\n']:
                    # Suppose table ended with empty line
                    # Note: we also reset the in_log_table for the DS/US
                    # channel status table above
                    if (not in_ds_stat_table) or (in_ds_stat_table and \
                        table_entry_processed and (not last_ln_messed)):
                        in_log_table = False
                elif not (in_ds_stat_table or in_us_stat_table):
                    # Still table line, remove it
                    # Update for the next line
                    last_line_empty = False
                    continue

            #
            # Remove title line of specific tables
            #
            if ptn.PTN_TABLE_TITLE.match(newline):
                # Update for the next line
                last_line_empty = False
                continue

            #
            # Convert a nested line as primary if two more empty lines
            # proceeded
            #
            if ptn.PTN_NESTED_LINE.match(newline):
                if last_line_empty and (con_empty_ln_cnt >= 2):
                    # Try to see if there are any exceptions
                    if not ptn.PTN_NESTED_LINE_EXCEPTION.match(newline):
                        newline = newline.lstrip()

            #
            # Convert some specific nested lines as primary
            #
            if ptn.PTN_NESTED_TO_PRI.match(newline):
                newline = newline.lstrip()

            #
            # Indent some specific lines
            #
            if ptn.PTN_PRI_TO_NESTED.match(newline):
                # Indent this line
                newline = ' ' + newline

            #
            # Indent a block of lines from primary to embedded
            #
            # Note: Do not indent the first line.
            # Empty line ends the block.
            if ptn.PTN_BLOCK_INDENT.match(newline):
                in_log_block3 = True
            elif in_log_block3:
                # Empty line ends the block
                if newline in ['\n', '\r\n']:
                    in_log_block3 = False
                else:
                    newline = ' ' + newline

            #
            # Indent a block of lines from primary to embedded
            #
            # Note: Do not indent the first line.
            # Special line (inclusive) ends the block.
            if ptn.PTN_BLOCK_INDENT2.match(newline):
                in_log_block4 = True
            elif in_log_block4:
                if ptn.PTN_BLOCK_INDENT2_END.match(newline):
                    # Special line ends the block
                    newline = ' ' + newline
                    in_log_block4 = False
                else:
                    newline = ' ' + newline

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
                    label_match = ptn.PTN_LABEL.search(curr_line_ts)
                    if label_match:
                        last_label = label_match.group(0)
                        last_label_removed = True

                # Update last_line_empty for the next line processing
                last_line_empty = True
                continue

            #
            # Line removing (including empty) should precede here
            # Update last_line_empty for the next line processing
            #
            last_line_empty = False

            #
            # Split some tokens apart
            #
            for ptn_obj in ptn.PTN_SPLIT_LEFT:
                mtch = ptn_obj.search(newline)
                if mtch:
                    newline = ptn_obj.sub(mtch.group(0)+' ', newline)

            for ptn_obj in ptn.PTN_SPLIT_RIGHT:
                mtch = ptn_obj.search(newline)
                if mtch:
                    newline = ptn_obj.sub(' '+mtch.group(0), newline)

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
            self.newlogs.append(newline)

            # The raw line index list in the new file
            # Do it only for prediction in DeepLog/Loglab and OSS
            if self.context in ['LOGLAB', 'OLDSCHOOL', 'DEEPLOG'] \
                and not (self.training or self.metrics):
                self.raw_ln_idx_new.append(idx+1)

        pbar.close()

        with open(self.fzip['new'], 'w', encoding='utf-8') as fnew:
            fnew.writelines(self.newlogs)

        print('Purge costs {!s}\n'.format(datetime.now()-parse_st))
