# Licensed under the MIT License - see License.txt
""" Base class of modern analyzing techniques.
"""
import os
import logging
from abc import ABC, abstractmethod
from typing import List
import shutil
import numpy as np
import pandas as pd
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh


__all__ = ["ModernBase"]


log = logging.getLogger(__name__)

# pylint: disable=too-many-instance-attributes
class ModernBase(ABC):
    """ The base class of modern analyzing techniques. """
    def __init__(self, df_raws, df_tmplts):
        self.fzip: dict = dh.get_files_io()
        self.training: bool = GC.conf['general']['training']
        self.metrics: bool = GC.conf['general']['metrics']
        self.context: str = GC.conf['general']['context']
        self.libsize: int = GC.conf['template']['size']

        # The in-memory structured norm raw logs from parser module
        self._df_raws = df_raws

        # By default, we use the in-memory dataframe of structured norm
        # and template lib. But for prediction, always use file library
        if not GC.conf['general']['aim']:
            # Read columns from normalized / structured log file
            self._df_raws = pd.read_csv(self.fzip['structured'],
                                usecols=['Content', 'EventId', 'EventTemplate'],
                                engine='c', na_filter=False, memory_map=True)
            # Read EventId from template library file
            self._df_tmplts = pd.read_csv(dh.TEMPLATE_LIB, usecols=['EventId'],
                                engine='c', na_filter=False, memory_map=True)
        elif not self.training:
            # Read EventId from template library file
            self._df_tmplts = pd.read_csv(dh.TEMPLATE_LIB, usecols=['EventId'],
                                engine='c', na_filter=False, memory_map=True)
        else:
            # The in-memory template lib from parser module
            self._df_tmplts = df_tmplts

        # For prediction only.
        if not self.training:
            self._raw_ln_idx_norm: List[int] = []


    def load_vocab(self, vocab_file: str, event_id_lib: List[str]):
        """ Generate/Load/Update vocabulary of eid (event id)

        Arguments
        ---------
        vocab_file: the path/name of vocabulary file
        event_id_lib: the event id list loaded from template library

        Returns
        -------
        event_id_shuffled: shuffled version of eid list with fixed size
        """
        if not os.path.exists(vocab_file):
            # Initialize shuffled EventId list of templates
            print('Building shuffled EventId list of templates.')

            # We should not get here for prediction
            if not self.training:
                print("Warning: No existing vocabulary for prediction. \
                       Something wrong!")

            # Init STIDLE: Shuffled Template Id List Expanded. Pad ZEROs
            # at the end of event_id_templates to expand the size to
            # TEMPLATE_LIB_SIZE. event_id_shuffled is a new list copy.
            event_id_shuffled = event_id_lib \
                                + ['0'] * (self.libsize - len(event_id_lib) -1)

            # Shuffle the expanded list event_id_shuffled in-place
            np.random.default_rng().shuffle(event_id_shuffled)
            # Reserve the last element (no shuffle) as value 'ffffffff'
            event_id_shuffled.append('ffffffff')

            np.save(vocab_file, event_id_shuffled)
            np.savetxt(vocab_file+'.txt', event_id_shuffled, fmt="%s")

            return event_id_shuffled

        # Load the existing STIDLE and update it
        print('Loading shuffled EventId list of templates.')
        event_id_shuffled = np.load(vocab_file).tolist()

        # We only update STIDLE for train dataset currently
        if self.training:
            # Read the EventIdOld column from template library
            event_id_lib_old = self._df_tmplts['EventIdOld'].to_list()
            update_flag = False

            # Case 1):
            # Find ZERO values in EventIdOld and the corresponding non
            # ZERO EventId
            event_id_old_zero = \
                [event_id_lib[idx] for idx, tid in enumerate(event_id_lib_old) if tid == '0']

            # There are ZEROs in EventIdOld. It means the corresponding
            # EventId is new. No need check the correspinding EventId is
            # non-ZERO.
            if len(event_id_old_zero) > 0:
                # Aggregate all idx of ZERO in STIDLE to a new list copy
                # then shuffle it.
                idx_zero_shuffled = \
                    [idx for idx, tid in enumerate(event_id_shuffled) if tid == '0']
                # Shuffle the idx_zero_shuffled in-place
                np.random.default_rng().shuffle(idx_zero_shuffled)
                # Insert the new EventId to the STIDLE
                updt_cnt = 0
                for idx, tid in enumerate(event_id_old_zero):
                    # Make sure no duplicates in the STIDLE
                    try:
                        event_id_shuffled.index(tid)
                    except ValueError:
                        event_id_shuffled[idx_zero_shuffled[idx]] = tid
                        updt_cnt += 1
                # Set the update flag
                update_flag = True
                print("%d new template IDs are inserted to STIDLE." % updt_cnt)

            # Case 2):
            # Find non ZEROs in EventIdOld that aren't equal to the ones
            # in EventId. Replace the old tid with the new one in STIDLE
            updt_cnt = 0
            for tid_old, tid in zip(event_id_lib_old, event_id_lib):
                if tid_old not in('0', tid):
                    idx_old = event_id_shuffled.index(tid_old)
                    event_id_shuffled[idx_old] = tid
                    updt_cnt += 1

            if updt_cnt > 0:
                # Set the update flag
                update_flag = True
                print("%d existing template IDs are updated in STIDLE." % updt_cnt)

            # Case 3):
            # TBD

            # Case 4):
            # TBD

            # Update the STIDLE file
            if update_flag:
                shutil.copy(vocab_file+'.txt', vocab_file+'.txt.old')
                np.save(vocab_file, event_id_shuffled)
                np.savetxt(vocab_file+'.txt', event_id_shuffled, fmt="%s")

        return event_id_shuffled


    @property
    def raw_ln_idx_norm(self):
        """ Get the raw line index in norm data """
        return self._raw_ln_idx_norm


    @raw_ln_idx_norm.setter
    def raw_ln_idx_norm(self, raw_ln_idx_norm: List[int]):
        """ Set the raw line index in norm data """
        self._raw_ln_idx_norm = raw_ln_idx_norm


    @abstractmethod
    def load_data(self):
        """ Extract features, vectoring, and compose data matrix.
        """


    @abstractmethod
    def train(self):
        """ Train the model.
        """


    @abstractmethod
    def predict(self):
        """ Predict using the trained model.
        """
