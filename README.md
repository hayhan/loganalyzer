# **Log Analyzer**

## **Usage**

### Raw log format prerequisite
Add timestamp like this one "[20190719-08:58:23.748] " at the start of each line. This not always necessary as we support arbitrary timestamp format including no timestamp for prediction of DeepLog and OSS (Old School System) now.

### Label your training logs
Put a string "abn: " after the timestamp for the anomaly log. If it is a multi-line log, we just label the first line. The labeling is needed for the classical machine learning models but not for the DeepLog training and OSS. While for validation purpose, the labeling is always needed.

### Train / Validate the model

**# Classical Machine Learning: (Loglizer)**

1) copy the labeled training logs file to logs/LOG_TYPE/train.txt. Copy the labeled validating logs file to logs/LOG_TYPE/test.txt.
2) run entrance/LOG_TYPE/train_unix.sh or train_win.bat
3) scripts above have some parameters that you can change, e.g. select different model, window size, etc.

**# Deep Learning: (DeepLog)**

1) put the training logs to logs/raw/LOG_TYPE/
2) run entrance/LOG_TYPE/deeplog_exec_train.sh or .bat

### Prediction

**# Classical Machine Learning: (Loglizer)**

1) copy the raw logs file to logs/LOG_TYPE/test.txt.
2) run entrance/LOG_TYPE/pred_unix.sh or pred_win.bat
3) anomalies are save to results/test/LOG_TYPE/anomaly_timestamp.csv

**# Deep Learning: (DeepLog)**

1) copy the raw logs file to logs/LOG_TYPE/test.txt
2) run entrance/LOG_TYPE/deeplog_exec_pred.sh or .bat
3) anomalies are save to results/test/LOG_TYPE/anomaly_result.txt

**# Old School System: (OSS)**

1) copy the raw logs file to logs/LOG_TYPE/test.txt
2) run entrance/LOG_TYPE/old_school.sh or .bat
3) results are save to results/test/LOG_TYPE/analysis_summary.csv

## **Porting to Other Systems**

LOG_TYPE currently supports 'cm' only. To analyze other system's logs, we need port application dependent files in new LOG_TYPE folders:

logparser/LOG_TYPE/
oldschool/LOG_TYPE/
entrance/LOG_TYPE/

## **Running Environment**

**# Python version**

3.6 or above

**# Basics packages**

pip install --upgrade numpy scipy scikit-learn pandas matplotlib tqdm skl2onnx onnxruntime

**# PyTorch**

see https://pytorch.org/ for install instructions. The version is 1.5.0 or above.

