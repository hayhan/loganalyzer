# Licensed under the MIT License - see LICENSE.txt
""" Derived class of preprocess. LOG_TYPE specific.
"""
import os
import logging
from typing import Any, List, Dict
import analyzer.utils.data_helper as dh
from analyzer.preprocess import PreprocessBase
from . import patterns as ptn
from . import misc as msc


__all__ = ["Preprocess"]

log = logging.getLogger(__name__)


class Preprocess(PreprocessBase):
    """ The class of preprocess. """
    def __init__(self):
        PreprocessBase.__init__(self)
        self.ptn_main_ts = ptn.PTN_STD_TS

    # pylint: disable=too-many-statements, disable=too-many-branches
    def process_for_domain(self, line: str, state: Dict[str, Any]):
        """ Special line process for LOG_TYPE """
        #
        # Because of host system code bug of no endl, some primary logs
        # are concatenated to the former one. We Split them and only
        # reserve the last log in the same line. Skip the match at the
        # position 0 if exists as we will remove it later. Also exclude
        # the case that tables are involved.
        #
        if ptn.PTN_BFC_TS.search(line, 2) \
            and not ptn.PTN_NESTED_LINE.match(line) \
            and not ptn.PTN_TABLE_TITLE_COMMON.match(line):
            #
            match_g = ptn.PTN_BFC_TS.finditer(line, 2)
            *_, last_match = match_g
            line = line[last_match.start() :]

        #
        # Remove other timestamps, console prompt and unwanted chars
        #
        line = ptn.PTN_CLEAN_CHAR.sub('', line)

        #
        # Remove unwanted log blocks. Specific lines end the block
        #
        if ptn.PTN_BLOCK_RM_START.match(line):
            state['in_log_blk'] = msc.LOG_BLK
            # Delete current line
            state['remove_line'] = True
        elif state['in_log_blk'] == msc.LOG_BLK:
            if ptn.PTN_BLOCK_RM_END.match(line):
                state['in_log_blk'] = msc.LOG_BLK_RST
            else:
                # Delete current line
                state['remove_line'] = True

        #
        # Remove unwanted log blocks. Primary line ends the block
        #
        elif ptn.PTN_BLOCK_RM_PRI.match(line):
            state['in_log_blk'] = msc.LOG_BLK2
            # Delete current line
            state['remove_line'] = True
        elif state['in_log_blk'] == msc.LOG_BLK2:
            if not ptn.PTN_NESTED_LINE.match(line) and line not in ['\n', '\r\n']:
                state['in_log_blk'] = msc.LOG_BLK_RST
            else:
                # Delete current line
                state['remove_line'] = True

        #
        # Remove line starting with specific patterns
        #
        elif ptn.PTN_LINE_RM.match(line):
            # Take care if the removed line has segment label. Hand
            # it over to the next line.
            if self.context in ['LOGLAB', 'DEEPLOG'] and (self.training or self.metrics):
                state['last_label'], state['last_label_removed'] \
                    = self._hand_over_label(state['curr_line_ts'])
            state['remove_line'] = True

        #
        # Indent a block of lines from primary to embedded. Note:
        # Do not indent the first line. Empty line ends the block.
        #
        elif ptn.PTN_BLOCK_INDENT.match(line):
            state['in_log_blk'] = msc.LOG_BLK_INDENT
        elif state['in_log_blk'] == msc.LOG_BLK_INDENT:
            # Empty line ends the block
            if line in ['\n', '\r\n']:
                state['in_log_blk'] = msc.LOG_BLK_RST
            else:
                line = ''.join([' ', line])

        #
        # Indent a block of lines from primary to embedded. Note:
        # Do not indent the first line. Special line (inclusive)
        # ends the block.
        #
        elif ptn.PTN_BLOCK_INDENT2.match(line):
            state['in_log_blk'] = msc.LOG_BLK_INDENT2
        elif state['in_log_blk'] == msc.LOG_BLK_INDENT2:
            if ptn.PTN_BLOCK_INDENT2_END.match(line):
                # Special line ends the block
                line = ''.join([' ', line])
                state['in_log_blk'] = msc.LOG_BLK_RST
            else:
                line = ''.join([' ', line])

        #
        # Indent some specific lines
        #
        elif ptn.PTN_PRI_TO_NESTED.match(line):
            # Indent this line
            line = ''.join([' ', line])

        #
        # Format DS channel status table
        #
        elif ptn.PTN_DS_CHAN_TABLE_START.match(line):
            state['in_stat_tbl'] = msc.LOG_TBL_DS
            # Remove the title line
            state['remove_line'] = True
        elif state['in_stat_tbl'] == msc.LOG_TBL_DS:
            line, \
            state['in_stat_tbl'], \
            state['tbl_hdr_done'], \
            state['remove_line'] \
                = self.format_chan_stat_table(
                line, state['in_stat_tbl'], state['tbl_hdr_done'],
                state['remove_line'], ptn.PTN_DS_CHAN_TABLE_END.match(line), 'DS'
            )

        #
        # Format US channel status table
        #
        elif ptn.PTN_US_CHAN_TABLE_START.match(line):
            state['in_stat_tbl'] = msc.LOG_TBL_US
            # Remove the title line
            state['remove_line'] = True
        elif state['in_stat_tbl'] == msc.LOG_TBL_US:
            line, \
            state['in_stat_tbl'], \
            state['tbl_hdr_done'], \
            state['remove_line'] \
                = self.format_chan_stat_table(
                line, state['in_stat_tbl'], state['tbl_hdr_done'],
                state['remove_line'], ptn.PTN_US_CHAN_TABLE_END.match(line), 'US'
            )

        #
        # Remove other tables. Should be behind DS/Us chan tables.
        #
        elif ptn.PTN_TABLE_TITLE_COMMON.match(line):
            state['in_log_blk'] = msc.LOG_BLK_TITLE
            # Remove the title line
            state['remove_line'] = True
        elif state['in_log_blk'] == msc.LOG_BLK_TITLE:
            if line in ['\n', '\r\n']:
                # Suppose table ended with empty line
                state['in_log_blk'] = msc.LOG_BLK_RST
            else:
                # Still table line, remove it
                state['remove_line'] = True

        #
        # Remove title line of specific tables
        #
        elif ptn.PTN_TABLE_TITLE.match(line):
            state['remove_line'] = True

        #
        # Convert some specific nested lines as primary
        #
        elif ptn.PTN_NESTED_TO_PRI.match(line):
            line = line.lstrip()

        #
        # Convert nested as primary if two more empty lines procede
        #
        elif ptn.PTN_NESTED_LINE.match(line) and state['last_ln_empty'] \
            and (state['con_empty_ln_cnt']>=2):
            # Try to see if there are any exceptions
            if not ptn.PTN_NESTED_LINE_EXCEPTION.match(line):
                line = line.lstrip()

        return line

    # pylint: disable=too-many-arguments
    def format_chan_stat_table(self, line: str, in_ch_stat_tbl: bool, tbl_hdr_done: bool,
                               remove_line: bool, is_table_end: bool, chan: str):
        """ Common entry for ds/us channel status table formating """
        if is_table_end:
            # End the table with specific line and reset states
            in_ch_stat_tbl = msc.LOG_TBL_RST
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
            return line, True

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
                return line, True

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
            return line, True

        if lineview[6] == '-':
            # For OFDMA channel, split it again. Suppose no messing.
            lineview = line.split(None, 10)
            # Split the last column again if it is an old stat table
            if lineview[10] not in ['y\n', 'n\n', 'y\r\n', 'n\r\n']:
                lineview[10], is_ok = self.format_legacy_table(lineview[10])
                if not is_ok:
                    # Bail out early and remove this line
                    return line, True

            line = ''.join(self.us_chan_log_ofdma(lineview))
        else:
            # For SC-QAM channel. Suppose no messing.
            # Split the last column again if it is an old stat table
            if lineview[8] not in ['y\n', 'n\n', 'y\r\n', 'n\r\n']:
                lineview[8], is_ok = self.format_legacy_table(lineview[8])
                if not is_ok:
                    # Bail out early and remove this line
                    return line, True

            line = ''.join(self.us_chan_log_scqam(lineview))
        return line, remove_line

    @staticmethod
    def format_legacy_table(last_col: str):
        """ Format legacy channel table, openbfc 17.4 and older """
        status: bool = True
        subview = last_col.split(None, 2)
        if subview[1][0] == 'y':
            last_col = 'y\n'
        elif subview[1][0] == 'n':
            last_col = 'n\n'
        else:
            status = False
        return last_col, status

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

    def split_tokens(self, line: str, lite: bool):
        """ Split some token apart per the regx patterns """
        if lite:
            line = self.split_token_apart(line, ptn.PTN_SPLIT_LEFT_TS,
                                          ptn.PTN_SPLIT_RIGHT_TS)
        else:
            line = self.split_token_apart(line, ptn.PTN_SPLIT_LEFT,
                                          ptn.PTN_SPLIT_RIGHT)
        return line

    def clean_misc_char(self, line: str):
        """ Clean console prompt, unwanted chars, etc """
        return ptn.PTN_CLEAN_CHAR.sub('', line)

    def match_session_label(self, line: str):
        """ Match session label for DeepLog """
        return ptn.PTN_SESSION.match(line)
