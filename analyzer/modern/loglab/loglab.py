# Licensed under the MIT License - see License.txt
""" Loglab module
"""
import os
import logging
from typing import List
from importlib import import_module
import pickle
import numpy as np
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh
from analyzer.modern import ModernBase

# Import the knowledge base for the corresponding log type
kb = import_module("analyzer.oldschool." + dh.LOG_TYPE + ".knowledgebase")

__all__ = ["Loglab"]


log = logging.getLogger(__name__)

class Loglab(ModernBase):
    """ The class of Loglab technique """
    def __init__(self, df_raws, df_tmplts, segll: List[tuple], dbg: bool = False):
        self.model: str = GC.conf['loglab']['model']
        self.win_size: int = GC.conf['loglab']['window_size']
        self.weight: int = GC.conf['loglab']['weight']
        self.dbg: bool = dbg
        self._segll: List[tuple] = segll

        ModernBase.__init__(self, df_raws, df_tmplts)


    def load_data(self):
        """
        Extract features, vectoring, and compose data matrix.

        Returns
        -------
        event_matrix: multi-line for training / validation, one line
                      matrix for prediction
        class_vector: vector of target class for each sample
        """
        # --------------------------------------------------------------
        # Load data from parser or files
        # --------------------------------------------------------------
        event_id_logs: List[str] = self._df_raws['EventId'].tolist()
        event_id_lib: List[str] = self._df_tmplts['EventId'].tolist()

        # --------------------------------------------------------------
        # Load vocab, aka STIDLE: Shuffled Template Id List Expanded
        # --------------------------------------------------------------
        event_id_voc: List[str] = self.load_vocab(dh.VOCAB_LOGLAB, event_id_lib)
        # event_id_voc = event_id_lib

        # Count the non-zero event id number in the vocabulary. Suppose
        # at least one zero element exists in the voc.
        # voc_size = len(set(event_id_voc)) - 1
        # voc_size = len(set(event_id_voc))

        # Convert event id (hash value) log vector to event index (0
        # based) log vector. For training data the template library/
        # vocabulary normally contain all the possible event ids. For
        # validation/test data, they might not retrive some ones. Map
        # the unknow event ids to the last index in the vocabulary.
        event_idx_logs = []
        for tid in event_id_logs:
            try:
                event_idx_logs.append(event_id_voc.index(tid))
            except ValueError:
                print("Warning: Event ID {} is not in vocabulary!!!".format(tid))
                event_idx_logs.append(self.libsize-1)

        #---------------------------------------------------------------
        # Extract features
        #---------------------------------------------------------------
        # For training or validation, always handle multi-sample logs
        if self.training or self.metrics:
            event_matrix, class_vector = \
                self.extract_feature_multi(self._df_raws, event_id_voc, event_id_logs)
        # For prediction, we need to suppose it is always one sample
        else:
            event_matrix, class_vector = \
                self.extract_feature(self._df_raws, event_id_voc, event_id_logs)

        return event_matrix, class_vector


    # pylint: disable=too-many-locals
    def extract_feature(self, data_df, eid_voc, eid_logs, sample_offset=0):
        """ Extract feature in one sample

        Arguments
        ---------
        data_df: data frame structured logs
        eid_voc: event id vocabulary
        eid_logs: event ids in structured logs
        sample_offset: the offset of current sample in the monolith

        Returns
        -------
        event_count_vec: one line matrix, aka. one sampe
        class_vec: empty
        """

        # Initialize the matrix for one sample
        event_count_vec = np.zeros((1,len(eid_voc)))

        # pylint: disable=too-many-nested-blocks
        for axis, line in data_df.iterrows():
            #
            # The sliced pandas dataframe of one sample still contrains
            # the absolute index of monolith. Convert it to the relative
            # index of log in current sample.
            axis -= sample_offset

            log_content_l = line['Content'].strip().split()
            log_event_tmplt_l = line['EventTemplate'].strip().split()
            event_id = line['EventId']

            if len(log_content_l) != len(log_event_tmplt_l):
                continue

            # Traverse all <*> tokens in log_event_tmplt_l and save the
            # index. Consider cases like '<*>;', '<*>,', etc. Remove the
            # unwanted ';,' in knowledgebase.
            idx_list = [idx for idx, value in enumerate(log_event_tmplt_l) if '<*>' in value]
            # print(idx_list)
            param_list = [log_content_l[idx] for idx in idx_list]
            # print(param_list)

            # Now we search in the knowledge base for the current log
            typical_log_hit, _, _ = kb.domain_knowledge(event_id, param_list)

            # If current log is hit in KB, we call it typical log and
            # add window around it.
            if typical_log_hit:
                # print('line {} hit, eid {}.'.format(axis+1, event_id))

                # Capture the logs within the window. The real window
                # size around typical log is 2*WINDOW_SIZE+1. That is,
                # there are WINDOW_SIZE logs respectively before and
                # after current typical log.

                # The axis part, it is also the typical log
                event_count_vec[0, eid_voc.index(event_id)] = self.weight

                # The upper part of the window
                for i in range(self.win_size):
                    if axis - (i+1) >= 0:
                        # Skip the event id which is not in the tempalte
                        # lib/vocabulary. This usually happens in the
                        # logs for prediction.
                        try:
                            feature_idx = eid_voc.index(eid_logs[axis-(i+1)])
                            if event_count_vec[0, feature_idx] == 0:
                                event_count_vec[0, feature_idx] = 1
                        except ValueError:
                            continue

                # The under part of the window
                for i in range(self.win_size):
                    if axis + (i+1) < len(eid_logs):
                        # Skip the event id which is not in the tempalte
                        # lib/vocabulary. This usually happens in the
                        # logs for prediction.
                        try:
                            feature_idx = eid_voc.index(eid_logs[axis+(i+1)])
                            if event_count_vec[0, feature_idx] == 0:
                                event_count_vec[0, feature_idx] = 1
                        except ValueError:
                            continue

        # Empty target class for prediction
        class_vec = []

        if self.dbg:
            self.print_ecm(event_count_vec, eid_voc)

        return event_count_vec, class_vec


    def extract_feature_multi(self, data_df, eid_voc, eid_logs):
        """
        Extract features in a monolith which always has multi samples

        Arguments
        ---------
        data_df: data frame structured logs, monolith
        eid_voc: event id vocabulary
        eid_logs: event ids in structured logs, monolith

        Returns
        -------
        event_count_matrix: multi-line (samples) for training/validation
        class_vector: vector of target class for each sample, int
        """

        # Load the sample info vector we generate in logparser module
        if not GC.conf['general']['aim']:
            with open(self.fzip['segll'], 'rb') as fin:
                self._segll = pickle.load(fin)
        # print(self._segll)

        # The sample info format: [(sample_size, sample_class), ...]
        # sample_size is int and unit is log, aka. one line in norm.
        # sample_class is str and is int after removing heading 'c'.

        # Initialize the matrix for multiple samples
        event_count_matrix = np.zeros((len(self._segll),len(eid_voc)))
        class_vec = []
        samoffset = 0

        # Traverse each sample in the monolith of training dataset
        for idx, saminfo in enumerate(self._segll):
            #
            # Extract class label for each training sample
            class_vec.append(int(saminfo[1][1:]))

            # Slice event id and dataframe of a sample from the monolith
            eid_sample = eid_logs[samoffset: samoffset+saminfo[0]]
            data_df_sample = data_df[samoffset: samoffset+saminfo[0]]

            # Do feature extraction for current sample
            event_count_matrix[idx], _ \
                = self.extract_feature(data_df_sample, eid_voc, eid_sample, samoffset)

            # Calc offset for the next sample in the monolith
            samoffset += saminfo[0]

        return event_count_matrix, class_vec


    @staticmethod
    def print_ecm(ecm, eid_voc):
        """ Print non-zero values in event count matrix
        """
        for idx, val in enumerate(ecm[0]):
            if val != 0.:
                print("ECM: idx -> {}, eid -> {}, val -> {}".format(idx, eid_voc[idx], val))


    def train(self):
        """ Train the model.
        """
        print("===> Train Loglab Model: {}\n".format(self.model))

        #---------------------------------------------------------------
        # Load data and do feature extraction on the training dataset
        #---------------------------------------------------------------

        # x_train data type is float while y_train is integer here
        x_train, y_train = self.load_data()

        # Save the event count matrix
        if self.dbg:
            np.savetxt(os.path.join(self.fzip['output'], 'ecm_loglab.txt'), x_train, fmt="%s")


    def predict(self):
        """ Predict using the trained model.
        """
        print(self.weight)
