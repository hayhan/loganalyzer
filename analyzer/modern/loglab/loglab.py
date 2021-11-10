# Licensed under the MIT License - see LICENSE.txt
""" Loglab module
"""
import os
import sys
import logging
from typing import List, Dict
from importlib import import_module
import pickle
import numpy as np
from tqdm import tqdm
# import matplotlib.pyplot as plt
# from sklearn.preprocessing import StandardScaler
from sklearn import svm, utils
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold, cross_val_score
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh
from analyzer.modern import ModernBase

# Import the knowledge base for the corresponding log type
kb = import_module("analyzer.oldschool." + dh.LOG_TYPE + ".knowledgebase")


__all__ = ["Loglab"]

log = logging.getLogger(__name__)


class Loglab(ModernBase):
    """ The class of Loglab technique """
    def __init__(self, df_raws, df_tmplts, dbg: bool = False):
        self.model: str = GC.conf['loglab']['model']
        self.win_size: int = GC.conf['loglab']['window_size']
        self.weight: int = GC.conf['loglab']['weight']
        self._segll: List[tuple] = []

        # Trained models for deployment, aka. for prediction
        self.onnx_model: str = os.path.join(
            dh.PERSIST_DATA, 'loglab_'+self.model+'.onnx'
        )

        # Core feature extraction and covering methods
        self.feat: Dict[str, str] = {
            'name': GC.conf['loglab']['feature'],
            'cover': GC.conf['loglab']['cover']
        }

        self.kbase = kb.Kb()

        ModernBase.__init__(self, df_raws, df_tmplts, dbg)

    @property
    def segll(self):
        """ Get the segment info """
        return self._segll

    @segll.setter
    def segll(self, segll: List[tuple]):
        """ Set the segment info """
        self._segll = segll

    def load_para(self):
        """ Load/Update model parameters """
        self.model = GC.conf['loglab']['model']
        self.win_size = GC.conf['loglab']['window_size']
        self.weight = GC.conf['loglab']['weight']

        self.onnx_model = os.path.join(
            dh.PERSIST_DATA, 'loglab_'+self.model+'.onnx'
        )

        self.feat = {
            'name': GC.conf['loglab']['feature'],
            'cover': GC.conf['loglab']['cover']
        }

    def load_data(self):
        """
        Extract features, vectoring, and compose data matrix.

        Returns
        -------
        event_matrix: multi-line for training / validation, one line \
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

        # Check if event ids are all in vocab. For training data, the
        # template library/vocabulary normally contain all the possible
        # event ids. For validation/test data, they may not contain all.
        for tid in event_id_logs:
            try:
                event_id_voc.index(tid)
            except ValueError:
                print(f"Warning: Event ID {tid} is not in vocabulary!!!")

        # --------------------------------------------------------------
        # Extract features
        # --------------------------------------------------------------
        # For training or validation, always handle multi-sample logs
        if self.training or self.metrics:
            event_matrix, class_vector = \
                self.extract_feature_multi(self._df_raws, event_id_voc)
        # For prediction, we suppose logs are not multi-target mixed
        else:
            event_matrix, class_vector = \
                self.extract_feature(self._df_raws, event_id_voc)

        return event_matrix, class_vector

    def extract_feature(self, data_df, eid_voc):
        """
        Extract feature in one sample

        Arguments
        ---------
        data_df: data frame structured logs
        eid_voc: event id vocabulary

        Returns
        -------
        event_count_vec: one line matrix, aka. event count in one sample
        class_vec: empty
        """

        if self.feat['name'] == 'BIN':
            event_count_vec = self.feature_core_binary(data_df, eid_voc)
        elif self.feat['name'] == 'CNT':
            event_count_vec = self.feature_core_count(data_df, eid_voc)
        else:
            print("This feature extraction is not supported!!! Abort!!!")
            sys.exit(1)

        # Empty target class for prediction
        class_vec = []

        if self.dbg:
            self.print_ecm(event_count_vec, eid_voc)

        return event_count_vec, class_vec

    # pylint: disable=too-many-locals
    def feature_core_binary(self, data_df, eid_voc):
        """
        Feature extraction core that does not count the event. It only
        checks if the event appears or not.

        Arguments
        ---------
        data_df: data frame structured logs
        eid_voc: event id vocabulary

        Returns
        -------
        event_count_vec: one line matrix, aka. event count in one sample
        """

        # Initialize the matrix for one sample
        event_count_vec = np.zeros((1,len(eid_voc)))

        # Prepare for the iteration. Extract info from dataframe.
        eid_logs = data_df['EventId'].tolist()
        tmplt_logs = data_df['EventTemplate'].tolist()
        cont_logs = data_df['Content'].tolist()

        # Do not iterate dataframe using iterrows(). It's very slow.
        for axis, (eid, tmplt, content) in enumerate(zip(eid_logs, tmplt_logs, cont_logs)):

            log_content_l = content.strip().split()
            log_tmplt_l = tmplt.strip().split()

            if len(log_content_l) != len(log_tmplt_l):
                continue

            # Traverse all <*> tokens in log_tmplt_l and save the index.
            # Consider cases like '<*>;', '<*>,', etc. Remove unwanted
            # char ';,' from param in knowledgebase if needed.
            idx_list = [idx for idx, value in enumerate(log_tmplt_l) if '<*>' in value]
            # print(idx_list)
            param_list = [log_content_l[idx] for idx in idx_list]
            # print(param_list)

            # Now we search in the knowledge base for the current log
            typical_log_hit, _ = self.kbase.domain_knowledge(eid, param_list)

            # If current log is hit in KB, we call it typical log and
            # add window around it.
            if typical_log_hit:
                # print(f"line {axis+1} hit, eid {eid}.")

                # Capture the logs within the window. The real window
                # size around typical log is 2*WINDOW_SIZE+1. That is,
                # there are WINDOW_SIZE logs respectively before and
                # after current typical log.

                # The axis part, it is also the typical log
                event_count_vec[0, eid_voc.index(eid)] = self.weight

                self.window_binary(axis, eid_voc, eid_logs, event_count_vec)

        return event_count_vec

    def feature_core_count(self, data_df, eid_voc):
        """
        Feature extraction core that counts the event and calculates the
        ratio to the whole sample that window sweeps.

        Arguments
        ---------
        data_df: data frame structured logs
        eid_voc: event id vocabulary

        Returns
        -------
        event_count_vec: one line matrix, aka. event count in one sample
        """

        # Initialize the matrix for one sample
        event_count_vec = np.zeros((1,len(eid_voc)))
        # Event/log character, 0: n/a, 1: aux, 2: typical
        event_char_voc: List[int] = [0] * len(eid_voc)
        # Event/log status in sample, 0: not counted, 1: counted
        event_stat_logs: List[int] = [0] * data_df.shape[0]

        # The edges that window sweeps in one samples
        edges = {'low': -1, 'high': -1}

        # Prepare for the iteration. Extract info from dataframe.
        eid_logs = data_df['EventId'].tolist()
        tmplt_logs = data_df['EventTemplate'].tolist()
        cont_logs = data_df['Content'].tolist()

        # Do not iterate dataframe using iterrows(). It's very slow.
        for axis, (eid, tmplt, content) in enumerate(zip(eid_logs, tmplt_logs, cont_logs)):

            log_content_l = content.strip().split()
            log_tmplt_l = tmplt.strip().split()

            if len(log_content_l) != len(log_tmplt_l):
                continue

            # Traverse all <*> tokens in log_tmplt_l and save the index.
            # Consider cases like '<*>;', '<*>,', etc. Remove unwanted
            # char ';,' from param in knowledgebase if needed.
            idx_list = [idx for idx, value in enumerate(log_tmplt_l) if '<*>' in value]
            # print(idx_list)
            param_list = [log_content_l[idx] for idx in idx_list]
            # print(param_list)

            # Now we search in the knowledge base for the current log
            typical_log_hit, _ = self.kbase.domain_knowledge(eid, param_list)

            # If current log is hit in KB, we call it typical log and
            # add window around it.
            if typical_log_hit:
                # print(f"line {axis+1} hit, eid {eid}.")

                if self.feat['cover'] == 'FULL':
                    # Update edges when window sweeps, otherwise we only
                    # sum the total counted logs together, aka. PART
                    self.edges_update(axis, edges, len(eid_logs))

                # Capture the logs within the window. The real window
                # size around typical log is 2*WINDOW_SIZE+1. That is,
                # there are WINDOW_SIZE logs respectively before and
                # after current typical log.

                # The axis part, it is also the typical log
                event_char_voc[eid_voc.index(eid)] = 2
                if event_stat_logs[axis] == 0:
                    event_count_vec[0, eid_voc.index(eid)] += 1
                    event_stat_logs[axis] = 1

                self.window_count(axis, eid_voc, eid_logs, event_count_vec,
                                  event_char_voc, event_stat_logs)

        if self.feat['cover'] == 'FULL':
            denom = edges['high']-edges['low']+1
        elif self.feat['cover'] == 'PART':
            denom = self.num_logs_counted(event_char_voc, event_count_vec)
        else:
            print("Cover method is not supported!!! Abort!!!")
            sys.exit(1)

        # Scale and weight the event count values
        self.weight_count(denom, event_char_voc, event_count_vec)

        return event_count_vec

    def window_binary(self, axis, eid_voc, eid_logs, event_count_vec):
        """
        Check event in binary manner within window, axis exclusive.

        Arguments
        ---------
        axis: the window axis
        eid_voc: event id vocabulary
        eid_logs: event id logs
        event_count_vec: one line matrix, aka. event count in one sample
        """

        for i in range(self.win_size):
            # The upper part of the window
            if axis - (i+1) >= 0:
                self.window_binary_core(
                    axis-(i+1), eid_voc, eid_logs, event_count_vec
                )

            # The under part of the window
            if axis + (i+1) < len(eid_logs):
                self.window_binary_core(
                    axis+(i+1), eid_voc, eid_logs, event_count_vec
                )

    # pylint: disable=too-many-arguments
    def window_count(self, axis, eid_voc, eid_logs, event_count_vec,
                     event_char_voc, event_stat_logs):
        """
        Count the event within window, axis exclusive.

        Arguments
        ---------
        axis: the window axis
        eid_voc: event id vocabulary
        eid_logs: event id logs
        event_count_vec: one line matrix, aka. event count in one sample
        event_char_voc: event charactor, 0: n/a, 1: aux, 2: typical
        event_stat_logs: log status in sample, 0: not counted 1: counted
        """

        for i in range(self.win_size):
            # The upper part of the window
            if axis - (i+1) >= 0:
                self.window_count_core(
                    axis-(i+1), eid_voc, eid_logs, event_count_vec,
                    event_char_voc, event_stat_logs
                )

            # The under part of the window
            if axis + (i+1) < len(eid_logs):
                self.window_count_core(
                    axis+(i+1), eid_voc, eid_logs, event_count_vec,
                    event_char_voc, event_stat_logs
                )

    @staticmethod
    def window_binary_core(idx, eid_voc, eid_logs, event_count_vec):
        """
        The core of windowing to do binary event count.

        Arguments
        ---------
        idx: the index
        eid_voc: event id vocabulary
        eid_logs: event id logs
        event_count_vec: one line matrix, aka. event count in one sample
        """

        # Skip the event id which is not in the tempalte lib or eid
        # vocabulary. This usually happens in the logs for prediction.
        try:
            feature_idx = eid_voc.index(eid_logs[idx])
            if event_count_vec[0, feature_idx] == 0:
                event_count_vec[0, feature_idx] = 1
        except ValueError:
            pass

    @staticmethod
    def window_count_core(idx, eid_voc, eid_logs, event_count_vec,
                          event_char_voc, event_stat_logs):
        """
        The core of windowing to do event count.

        Arguments
        ---------
        idx: the index
        eid_voc: event id vocabulary
        eid_logs: event id logs
        event_count_vec: one line matrix, aka. event count in one sample
        event_char_voc: event charactor, 0: n/a, 1: aux, 2: typical
        event_stat_logs: log status in sample, 0: not counted 1: counted
        """

        # Skip the event id which is not in the tempalte lib or eid
        # vocabulary. This usually happens in the logs for prediction.
        try:
            feature_idx = eid_voc.index(eid_logs[idx])
            if event_char_voc[feature_idx] == 0:
                event_char_voc[feature_idx] = 1
            if event_stat_logs[idx] == 0:
                event_count_vec[0, feature_idx] += 1
                event_stat_logs[idx] = 1
        except ValueError:
            pass

    def edges_update(self, axis: int, edges: dict, sample_len: int):
        """
        Update edges that window sweeps within one sample.

        Arguments
        ---------
        axis: the window axis
        edges: the low and high edges that window sweeps
        sample_len: length of sample
        """

        if edges['low'] == -1:
            tmp = axis - self.win_size
            edges['low'] = tmp if tmp >= 0 else 0

        tmp = axis + self.win_size
        edges['high'] = tmp if tmp < sample_len else sample_len - 1

    def weight_count(self, sweep_len: int, event_char_voc: List[int],
                     event_count_vec: np.ndarray):
        """
        Scale and weight the event count values in one sample.

        Arguments
        ---------
        sweep_len: the number of logs that window sweeps in one sample
        event_char_voc: event charactor, 0: n/a, 1: aux, 2: typical
        event_count_vec: one line matrix, aka. event count in one sample
        """

        for i, char in enumerate(event_char_voc):
            if bool(event_count_vec[0, i]) ^ bool(char):
                print("Something wrong in event counting!!! Abort!!!")
                sys.exit(1)
            if char == 1:
                master_weight = 1
            elif char == 2:
                master_weight = self.weight
            else:
                # char == 0 or undefined values (should not happen)
                continue

            event_count_vec[0, i] = event_count_vec[0, i]/sweep_len + master_weight

    @staticmethod
    def num_logs_counted(event_char_voc: List[int], event_count_vec: np.ndarray):
        """
        Sum the number of counted event in one sample.

        Arguments
        ---------
        event_char_voc: event charactor, 0: n/a, 1: aux, 2: typical
        event_count_vec: one line matrix, aka. event count in one sample

        Returns
        -------
        num: the number of counted event in one sample
        """

        num: int = 0
        for i, char in enumerate(event_char_voc):
            if char != 0:
                num += event_count_vec[0, i]

        return num

    def extract_feature_multi(self, data_df, eid_voc):
        """
        Extract features in a monolith which always has multi samples.

        Arguments
        ---------
        data_df: data frame structured logs, monolith
        eid_voc: event id vocabulary

        Returns
        -------
        event_count_matrix: multi-line (samples) for training/validation
        class_vec: vector of target class for each sample, int
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

        print("Extracting features...")

        # A lower overhead progress bar
        pbar = tqdm(total=len(self._segll), unit='Lines', disable=self.dbg,
                    bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

        # Traverse each sample in the monolith of training dataset
        for idx, saminfo in enumerate(self._segll):
            #
            # Extract class label for each training sample
            class_vec.append(int(saminfo[1][1:]))

            # Slice event id and dataframe of a sample from the monolith
            data_df_sample = data_df[samoffset: samoffset+saminfo[0]]

            # Do feature extraction for current sample
            event_count_matrix[idx], _ \
                = self.extract_feature(data_df_sample, eid_voc)

            # Calc offset for the next sample in the monolith
            samoffset += saminfo[0]

            pbar.update(1)

        pbar.close()

        return event_count_matrix, class_vec

    @staticmethod
    def print_ecm(ecm, eid_voc):
        """ Print non-zero values in event count matrix
        """
        for idx, val in enumerate(ecm[0]):
            if val != 0.:
                print(f"ECM: idx -> {idx}, eid -> {eid_voc[idx]}, val -> {val}")

    @staticmethod
    def mykfold(y_train, monolith_data, model):
        """ Leave-one-out cross validation """
        k = len(y_train)
        k_sample_count = monolith_data.shape[0] // k

        for fold in range(k):
            test_begin = k_sample_count * fold
            test_end = k_sample_count * (fold + 1)

            test_data = monolith_data[test_begin: test_end]

            train_data = np.vstack([
                monolith_data[:test_begin],
                monolith_data[test_end:]
            ])

            # Train the model with training data
            x_train = train_data[:, :-1]
            y_train = train_data[:, -1].astype(int)
            model.fit(x_train, y_train)

            # Validate the model with test data
            x_test = test_data[:, :-1]
            y_test = test_data[:, -1].astype(int)
            y_test_pred = model.predict(x_test)
            if y_test != y_test_pred:
                print(f"raw sample index {test_begin+1} of class {y_test} -> {y_test_pred}")

    def train(self):
        """ Train the model.
        """
        # Update selected model and its parameters
        self.load_para()

        print(f"===> Train Loglab Model: {self.model}\n")

        # --------------------------------------------------------------
        # Load data and do feature extraction on the training dataset
        # --------------------------------------------------------------

        # x_train data type is float while y_train is integer here
        x_train, y_train = self.load_data()

        # Visualize the sparse matrix
        # plt.spy(x_train, markersize=1)
        # plt.show()

        # Feature scaling
        # TBD:
        # scaler = StandardScaler()
        # x_train = scaler.fit_transform(x_train)

        # --------------------------------------------------------------
        # Select models and tune the parameters by cross validation
        # --------------------------------------------------------------
        if self.model == 'RFC':
            model = RandomForestClassifier(n_estimators=100)
        elif self.model == 'LR':
            model = LogisticRegression(penalty='l2', C=100, tol=0.01,
                        class_weight=None, solver='liblinear', max_iter=100,
                        multi_class='auto')
        elif self.model == 'SVM':
            model = svm.LinearSVC(penalty='l2', tol=0.0001, C=1, dual=True,
                        class_weight=None, max_iter=4000,
                        multi_class='ovr')
            # model = svm.LinearSVC()
            # model = svm.SVC()
        else:
            print("The model name is not defined. Exit.")
            sys.exit(1)

        # --------------------------------------------------------------
        # k-fold cross validation
        # We can use numpy, pandas or sklearn KFold api directly.
        # --------------------------------------------------------------

        # Convert class target list to column array and merge w/ x_train
        class_vec = np.reshape(y_train, (len(y_train), 1))
        # Monolith dataset is type of float including the last column,
        # which is class labels.
        monolith_data = np.hstack((x_train, class_vec))

        # Save the event count matrix for debugging before randomization
        if self.dbg:
            np.savetxt(os.path.join(self.fzip['output'], 'ecm_loglab.txt'),
                       monolith_data, fmt="%s")

        # Randomize the training samples
        monolith_data = utils.shuffle(monolith_data)
        if self.dbg:
            print(f"monolith_data: {monolith_data}\n"
                  f"len of monolith_data: {(monolith_data).shape}")

        print("Training...")

        if GC.conf['loglab']['mykfold']:
            self.mykfold(y_train, monolith_data, model)
        else:
            # Initialise the number of folds k for doing CV
            kfold = KFold(n_splits=monolith_data.shape[0])
            x_train = monolith_data[:, :-1]
            y_train = monolith_data[:, -1].astype(int)

            # Evaluate the model using k-fold CV
            scores = cross_val_score(model, x_train, y_train, cv=kfold, scoring='accuracy')

            # Get the model performance metrics
            print(scores)
            print("Mean: " + str(scores.mean()) + '\n')

        # --------------------------------------------------------------
        # Train the model with the optimized parameters in validation
        # and distrubute it
        # --------------------------------------------------------------
        x_train = monolith_data[:, :-1]
        y_train = monolith_data[:, -1].astype(int)
        model.fit(x_train, y_train)

        # Persist the model for deployment using sklearn-onnx converter
        # http://onnx.ai/sklearn-onnx/
        initial_type = [('float_input', FloatTensorType([None, x_train.shape[1]]))]
        onx = convert_sklearn(model, initial_types=initial_type)
        with open(self.onnx_model, "wb") as fout:
            fout.write(onx.SerializeToString())

    def evaluate(self):
        """ Validate the model.
        """
        log.info("Place holder.")

    def predict(self):
        """ Predict using the trained model.
        """
        # Update selected model and its parameters
        self.load_para()

        print(f"===> Predict With Loglab Model: {self.model}\n")

        # --------------------------------------------------------------
        # Load data and do feature extraction on the test dataset
        # --------------------------------------------------------------
        # Update the parameters of selected model
        self.load_para()

        x_test, _ = self.load_data()

        # Feature scaling based on training dataset
        # TBD:
        # scaler = StandardScaler()
        # x_test = scaler.transform(x_test)

        # Load ONNX model which is equivalent to the scikit-learn model
        # https://microsoft.github.io/onnxruntime/python/api_summary.html
        assert os.path.exists(self.onnx_model)
        sess = rt.InferenceSession(self.onnx_model)
        input_name = sess.get_inputs()[0].name

        # Target class
        label_name = sess.get_outputs()[0].name
        y_pred = sess.run([label_name], {input_name: x_test.astype(np.float32)})[0]
        print(y_pred)

        # Probability of each target class
        label_name = sess.get_outputs()[1].name
        y_pred_prob = sess.run([label_name], {input_name: x_test.astype(np.float32)})[0]
        print(y_pred_prob)

    def check_feature(self):
        """ Check the features of the dataset.
        """
        # Update the parameters of selected model
        self.load_para()
        self.load_data()
