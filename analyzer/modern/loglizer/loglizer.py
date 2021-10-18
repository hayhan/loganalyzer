# Licensed under the MIT License - see LICENSE.txt
""" Loglizer module
"""
import os
import sys
import logging
import pickle
from typing import List
from datetime import datetime
import joblib
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn import tree, svm
from sklearn.naive_bayes import MultinomialNB
# from sklearn.linear_model import Perceptron
from sklearn.linear_model import SGDClassifier, LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_fscore_support
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt
from analyzer.config import GlobalConfig as GC
import analyzer.utils.data_helper as dh
from analyzer.modern import ModernBase


__all__ = ["Loglizer"]

log = logging.getLogger(__name__)


# pylint: disable=too-many-instance-attributes
class Loglizer(ModernBase):
    """ The class of Loglizer technique """
    def __init__(self, df_raws, df_tmplts, dbg: bool = False):
        self.model: str = GC.conf['loglizer']['model']
        self.win_size: int = GC.conf['loglizer']['window_size']
        self.step_size: int = GC.conf['loglizer']['window_step']
        self.inc_updt: bool = False
        self._labels: List[int] = []
        self.win_idx: List[tuple] = []
        self.onnx_model: str = os.path.join(dh.PERSIST_DATA, 'loglizer_'+self.model+'.onnx')

        ModernBase.__init__(self, df_raws, df_tmplts, dbg)

    @property
    def labels(self):
        """ Get the label info """
        return self._labels

    @labels.setter
    def labels(self, labels: List[int]):
        """ Set the label info """
        self._labels = labels

    def load_para(self):
        """ Load/Update model parameters """
        self.model = GC.conf['loglizer']['model']
        self.win_size = GC.conf['loglizer']['window_size']
        self.step_size = GC.conf['loglizer']['window_step']
        self.onnx_model = os.path.join(dh.PERSIST_DATA, 'loglizer_'+self.model+'.onnx')
        if self.model in ['DT', 'LR', 'SVM', 'RFC']:
            self.inc_updt = False
        elif self.model in ['MNB', 'PTN', 'SGDC_SVM', 'SGDC_LR']:
            self.inc_updt = True
        else:
            log.error("Model is not supported. Exit.")
            sys.exit(1)

    def load_data(self):
        """
        Extract features, vectoring, and compose data matrix.

        Returns
        -------
        event_count_matrix: event count matrix, where each row is an \
                            instance (log sequence vector).
        labels: a list of labels, 1 represents anomaly
        """
        # --------------------------------------------------------------
        # Load data from parser or files
        # --------------------------------------------------------------
        event_id_logs: List[str] = self._df_raws['EventId'].tolist()
        event_id_lib: List[str] = self._df_tmplts['EventId'].tolist()

        self._df_raws['DT'] = pd.to_datetime(self._df_raws['Time'],
                                             format="[%Y%m%d-%H:%M:%S.%f]")
        # Convert timestamp to millisecond unit
        self._df_raws['Ms_Elapsed'] = ((self._df_raws['DT']-self._df_raws['DT'][0])
                                       .dt.total_seconds()*1000).astype('int64')

        # For prediction, init the label vector with ZEROs
        # For training or validation, read the real label vector
        if (not self.training) and (not self.metrics):
            self._df_raws['Label'] = [0] * self._df_raws.shape[0]
        else:
            if not GC.conf['general']['aim']:
                with open(self.fzip['labels'], 'rb') as fin:
                    self._labels = pickle.load(fin)
            self._df_raws['Label'] = self._labels

        raw_data = self._df_raws[['Label','Ms_Elapsed']].values

        # Do not calc the num of logs that are anomalies for prediction
        if self.training or self.metrics:
            print(f"The number of anomaly logs is {sum(raw_data[:, 0])}, "
                  f"but it requires further processing")

        # --------------------------------------------------------------
        # Load vocab, aka STIDLE: Shuffled Template Id List Expanded
        # --------------------------------------------------------------
        if self.inc_updt:
            event_id_voc: List[str] = self.load_vocab(dh.VOCAB_LOGLIZER, event_id_lib)
        else:
            if not os.path.exists(dh.VOCAB_LOGLIZER_STATIC):
                event_id_voc = np.random.default_rng().permutation(event_id_lib).tolist()
                np.save(dh.VOCAB_LOGLIZER_STATIC, event_id_voc)
            else:
                print('Loading shuffled EventId list in templates: static version.')
                event_id_voc = np.load(dh.VOCAB_LOGLIZER_STATIC).tolist()

        # --------------------------------------------------------------
        # Slice data using sliding window
        # --------------------------------------------------------------
        start_end_index_list, inst_number = self.slice_data(raw_data)

        # For prediction, we will use the window index info to locate
        # the anomaly in the raw logs.
        if not self.training and not self.metrics:
            self.win_idx = start_end_index_list

        # Prepare the further window index for matrix building
        expanded_indexes_list = self.all_log_idx(start_end_index_list, inst_number)

        # --------------------------------------------------------------
        # Build event count matrix
        # --------------------------------------------------------------
        ecm, labels = self.build_matrix(event_id_logs, event_id_voc, raw_data,
                                        inst_number, expanded_indexes_list)

        # --------------------------------------------------------------
        # Weight the event count matrixs
        # --------------------------------------------------------------
        if self.training:
            # Training only
            ecm = self.fit_transform(ecm, term_weighting='tf-idf')
        else:
            # Validation or Prediction
            ecm = self.transform(ecm, term_weighting='tf-idf')

        # Return the (x, y) to feed models
        return ecm, labels

    def slice_data(self, raw_data):
        """
        Slice data using sliding window

        Arguments
        ---------
        raw_data: np array of (label, time) of each log

        Returns
        -------
        start_end_index_list: start/end index of each window
        inst_number: the number of instance
        """
        # List of tuples, each contains two numbers representing the
        # start and end of sliding window.
        start_end_index_list: List[tuple] = []
        time_data = raw_data[:, 1]

        parse_st = datetime.now()
        # Split into sliding windows
        start_time = time_data[0]
        start_index = 0
        end_index = -1

        # Get the first start, end index, end time
        for cur_time in time_data:
            # Window end (end_time) selects the min if not equal
            if  cur_time <= start_time + self.win_size:
                end_index += 1
                # end_time = cur_time
            else:
                break
        start_end_pair=tuple((start_index, end_index))
        start_end_index_list.append(start_end_pair)

        # Move the start and end index until next sliding window
        while end_index < raw_data.shape[0] - 1:

            prev_win_start = start_index
            for cur_time in time_data[prev_win_start:]:
                # Window start (start_time) selects the max if not equal
                if cur_time < start_time + self.step_size:
                    start_index += 1
                else:
                    start_time = cur_time
                    break

            end_index = start_index - 1
            curr_win_start = start_index
            for cur_time in time_data[curr_win_start:]:
                # Window end (end_time) selects the min if not equal
                if cur_time <= start_time + self.win_size:
                    end_index += 1
                    # end_time = cur_time
                else:
                    break

            start_end_pair=tuple((start_index, end_index))
            start_end_index_list.append(start_end_pair)
            # print(start_end_index_list)

        inst_number = len(start_end_index_list)
        print(f"There are {inst_number} instances (sliding windows) "
              f"in this dataset, cost {datetime.now()-parse_st}.\n")

        return start_end_index_list, inst_number

    @staticmethod
    def all_log_idx(start_end_index_list: List[tuple], inst_number: int):
        """
        Get all the log indexes in each time window by ranging from
        start_index to end_index.
        """
        expanded_indexes_list=[]
        for _ in range(inst_number):
            index_list = []
            expanded_indexes_list.append(index_list)
        for i in range(inst_number):
            start_index = start_end_index_list[i][0]
            end_index = start_end_index_list[i][1]
            for j in range(start_index, end_index+1):
                expanded_indexes_list[i].append(j)

        return expanded_indexes_list

    # pylint: disable=too-many-arguments,too-many-locals
    def build_matrix(self, event_id_logs, event_id_voc, raw_data,
                     inst_number, expanded_indexes_list):
        """
        Build event count matrix
        """
        # Count the overall num of log events.
        event_num = len(list(set(event_id_logs)))
        print(f"There are {event_num} log events")

        # Get labels and event count of each sliding window
        labels = []
        label_data = raw_data[:, 0]
        event_count_matrix = np.zeros((inst_number,len(event_id_voc)))
        for j in range(inst_number):
            label = 0   # 0 represents success, 1 represents failure
            for k in expanded_indexes_list[j]:
                # Label the instance even if current log might not be in
                # train template lib.
                if label_data[k]:
                    label = 1
                # Current log EventId, aka. template id
                event_id = event_id_logs[k]
                # Convert EventId to ZERO based index in vocab
                try:
                    event_index = event_id_voc.index(event_id)
                except:  # pylint: disable=bare-except
                    log.warning('EventId %s is not in the templates of train data', event_id)
                    continue
                # Increase the feature/event/template count in event
                # count matrix.
                event_count_matrix[j, event_index] += 1
            # One label per instance. Labeling the instance if one log
            # within is labeled at least.
            labels.append(label)
        assert inst_number == len(labels)
        # Do not calc the num of instances that have anomalies on test
        # dataset w/o validating.
        if self.training or self.metrics:
            print(f"Among all instances, {sum(labels)} are anomalies")
        # assert event_count_matrix.shape[0] == len(labels)

        if self.dbg:
            label_vec = np.reshape(labels, (len(labels), 1))
            monolith_data = np.hstack((event_count_matrix, label_vec))

            np.savetxt(os.path.join(self.fzip['output'], 'ecm_loglizer.txt'),
                       monolith_data, fmt="%s")

        return event_count_matrix, labels

    def fit_transform(self, x_seq, term_weighting=None,
                      normalization=None):
        """ Fit and transform the data matrix

        Arguments
        ---------
        x_seq: ndarray, log sequences matrix
        term_weighting: None or `tf-idf`
        normalization: None or `zero-mean`

        Returns
        -------
        x_new: The transformed train data matrix
        """
        print('====== Transformed train data summary ======')

        # pylint: disable=invalid-name
        x = x_seq
        num_instance, num_event = x.shape
        # print(x.shape)
        if term_weighting == 'tf-idf':
            df_vec = np.sum(x > 0, axis=0)
            # print(df_vec)
            idf_vec = np.log(num_instance / (df_vec + 1e-8))
            idf_matrix = x * np.tile(idf_vec, (num_instance, 1))
            x = idf_matrix
            # _ToDo: incrementally update idf? Need evaluate.
            # Save the idf_vec for predict
            if self.inc_updt:
                np.save(os.path.join(dh.PERSIST_DATA, 'idf_vector_train.npy'), idf_vec)
            else:
                np.save(os.path.join(dh.PERSIST_DATA, 'idf_vector_train_static.npy'), idf_vec)
        if normalization == 'zero-mean':
            mean_vec_t = x.mean(axis=0)
            mean_vec = mean_vec_t.reshape(1, num_event)
            x = x - np.tile(mean_vec, (num_instance, 1))
        elif normalization == 'sigmoid':
            x[x != 0] = expit(x[x != 0])
        x_new = x
        # print(x_new)

        # x_data_file = self.fzip['output'] + 'train_x_data.txt'
        # np.savetxt(x_data_file, x_new, fmt="%s")
        print(f"Final train data shape: {x_new.shape[0]}-by-{x_new.shape[1]}\n")
        return x_new

    def transform(self, x_seq, term_weighting=None, normalization=None,
                  use_train_factor=True):
        """ Transform the data matrix with trained parameters

        Arguments
        ---------
        x_seq: log sequences matrix
        term_weighting: None or `tf-idf`
        normalization: None or `zero-mean`
        use_train_factor: Apply train dataset result

        Returns
        -------
        x_new: The transformed data matrix
        """
        print('====== Transformed test data summary ======')

        # pylint: disable=invalid-name
        x = x_seq
        num_instance, num_event = x.shape
        if term_weighting == 'tf-idf':
            if use_train_factor:
                # Load the idf vector of training stage from file
                if self.inc_updt:
                    idf_vec = np.load(os.path.join(dh.PERSIST_DATA, 'idf_vector_train.npy'))
                else:
                    idf_vec = np.load(os.path.join(dh.PERSIST_DATA, 'idf_vector_train_static.npy'))
                # print(idf_vec)
            else:
                # Use the idf data of test instead of the one from train data
                df_vec = np.sum(x > 0, axis=0)
                idf_vec = np.log(num_instance / (df_vec + 1e-8))
            idf_matrix = x * np.tile(idf_vec, (num_instance, 1))
            x = idf_matrix
        if normalization == 'zero-mean':
            # _ToDo: Use the mean_vec from train stage
            mean_vec_t = x.mean(axis=0)
            mean_vec = mean_vec_t.reshape(1, num_event)
            x = x - np.tile(mean_vec, (num_instance, 1))
        elif normalization == 'sigmoid':
            x[x != 0] = expit(x[x != 0])
        x_new = x
        # print(x_new)

        # x_data_file = self.fzip['output'] + 'test_x_data.txt'
        # np.savetxt(x_data_file, x_new, fmt="%s")
        print(f"Test data shape: {x_new.shape[0]}-by-{x_new.shape[1]}\n")

        return x_new

    # pylint: disable=too-many-branches
    def train(self):
        """ Train model.
        """
        # Update selected model and its parameters
        self.load_para()
        print(f"===> Train Model: {self.model}\n")

        # --------------------------------------------------------------
        # Load data, extract features and build event count matrix
        # --------------------------------------------------------------

        # x_train data type is float while y_train is integer here
        x_train, y_train = self.load_data()

        # --------------------------------------------------------------
        # Select models, set parameters
        # --------------------------------------------------------------

        # Load the saved complete scikit-learn model if it exists
        if self.inc_updt:
            inc_fit_model_file = \
                os.path.join(dh.PERSIST_DATA, 'loglizer_inc_'+self.model+'.object')
            all_classes = np.array([0, 1])

        # Incremental training at the 1st time
        if self.inc_updt and not os.path.exists(inc_fit_model_file):
            if self.model == 'MNB':
                model = MultinomialNB(alpha=1.0, fit_prior=True, class_prior=None)
            elif self.model == 'PTN':
                model = SGDClassifier(loss='perceptron', max_iter=1000)
            elif self.model == 'SGDC_SVM':
                model = SGDClassifier(loss='hinge', max_iter=1000)
            else:
                # SGDC_LR
                model = SGDClassifier(loss='log', max_iter=1000)
            print(f"First time training...: {self.model}\n")
        # Incremental training ...
        elif self.inc_updt:
            model = joblib.load(inc_fit_model_file)
            print(f"Incremental training...: {self.model}\n")
        # Normal training ...
        else:
            if self.model == 'DT':
                model = tree.DecisionTreeClassifier(criterion='gini', max_depth=None,
                            max_features=None, class_weight=None)
            elif self.model == 'LR':
                model = LogisticRegression(penalty='l2', C=100, tol=0.01,
                            class_weight=None, solver='liblinear', max_iter=100)
            elif self.model == 'SVM':
                model = svm.LinearSVC(penalty='l1', tol=0.1, C=1, dual=False,
                            class_weight=None, max_iter=100)
            else:
                # Random Forest Classifier
                model = RandomForestClassifier(n_estimators=100)
            print(f"Normal training...: {self.model}\n")

        # --------------------------------------------------------------
        # Fit and persist the model
        # --------------------------------------------------------------
        if self.inc_updt:
            # model.fit(x_train, y_train)
            model.partial_fit(x_train, y_train, classes=all_classes)
            # Save the model object for incremental learning
            joblib.dump(model, inc_fit_model_file)
        else:
            model.fit(x_train, y_train)

        # Persist model for deployment by using sklearn-onnx converter
        # http://onnx.ai/sklearn-onnx/
        initial_type = [('float_input', FloatTensorType([None, x_train.shape[1]]))]
        onx = convert_sklearn(model, initial_types=initial_type)
        with open(self.onnx_model, "wb") as fout:
            fout.write(onx.SerializeToString())

        # Validate itself
        y_train_pred = model.predict(x_train)
        print('Train validation:')
        # pylint: disable=invalid-name
        precision, recall, f1, _ = \
            precision_recall_fscore_support(y_train, y_train_pred, average='binary')

        print(f"Precision: {precision:.3f}, recall: {recall:.3f}, F1-measure: {f1:.3f}\n")

    def evaluate(self):
        """ Validate the model.
        """
        # Update selected model and its parameters
        self.load_para()
        print(f"===> Validate Model: {self.model}\n")

        # Extract features, build event count matrix
        x_test, y_test = self.load_data()

        # Load model
        # https://microsoft.github.io/onnxruntime/python/api_summary.html
        sess = rt.InferenceSession(self.onnx_model)
        input_name = sess.get_inputs()[0].name
        label_name = sess.get_outputs()[0].name
        y_test_pred = sess.run([label_name], {input_name: x_test.astype(np.float32)})[0]

        print('Test validation:')
        # pylint: disable=invalid-name
        precision, recall, f1, _ = \
            precision_recall_fscore_support(y_test, y_test_pred, average='binary')

        print(f"Precision: {precision:.3f}, recall: {recall:.3f}, F1-measure: {f1:.3f}\n")

    # pylint: disable=too-many-locals
    def predict(self):
        """ Predict using model.
        """
        # Update selected model and its parameters
        self.load_para()
        print(f"===> Predict Model: {self.model}\n")

        # Extract features, build event count matrix
        x_test, _ = self.load_data()

        # Load model
        # https://microsoft.github.io/onnxruntime/python/api_summary.html
        sess = rt.InferenceSession(self.onnx_model)
        input_name = sess.get_inputs()[0].name
        label_name = sess.get_outputs()[0].name
        y_test_pred = sess.run([label_name], {input_name: x_test.astype(np.float32)})[0]

        # Trace anomaly timestamp windows in the raw log file
        anomaly_window_list: List[tuple] = []
        for i, pred_result in enumerate(y_test_pred):
            if pred_result:
                start_index = self.win_idx[i][0]
                end_index = self.win_idx[i][1]
                anomaly_window_list.append(tuple((start_index, end_index)))

        norm_time_list = self._df_raws['Time'].to_list()

        anomaly_timestamp_list: List[tuple] = []
        for _, anomaly_window in enumerate(anomaly_window_list):
            # pylint: disable=invalid-name
            x = anomaly_window[0]
            y = anomaly_window[1]
            anomaly_timestamp_list.append(tuple((norm_time_list[x], norm_time_list[y])))

        # Save the final timestamp tuples of anomaly
        np.savetxt(self.fzip['rst_llzr'], anomaly_timestamp_list,
                   delimiter=',', fmt='%s')
