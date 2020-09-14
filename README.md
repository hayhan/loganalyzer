# **Log Analyzer**

## **Usage**

### Raw log format prerequisite
Add timestamp like this one "[20190719-08:58:23.748] " at the start of each line.

### Label your training logs
Put a string "abn: " after the timestamp for the anomaly log. If it is a multi-line log, just label the first line. The labeling is needed for the classical machine learning models but not for the DeepLog training and OSS (Old School System). For validation purpose, the labeling is always needed.

### Train / Validate the model

**# Classical Machine Learning**

1) copy the labeled training logs file to logs/train.txt. Copy the labeled validating logs file to logs/test.txt.
2) run entrance/train_unix.sh or train_win.bat
3) above scripts have some parameters that you can change, e.g. select different model, window size, etc

**# Deep Learning: (DeepLog)**

1) put the training logs to logs/raw/
2) run entrance/deeplog_exec_train.sh or .bat

### Predict

**# Classical Machine Learning**

1) copy the raw logs file to logs/test.txt.
2) run entrance/pred_unix.sh or pred_win.bat
3) anomalies are save to results/test/anomaly_timestamp.csv

**# Deep Learning: (DeepLog)**

1) copy the raw logs file to logs/test.txt
2) run entrance/deeplog_exec_pred.sh or .bat
3) anomalies are save to results/test/anomaly_result.txt

### The Old School System
The step 3) of Predict also runs the OSS to get another analyzing result, which is save to results/test/analysis_summary.csv.

## **Porting to Other Systems**

By default, the logs come from Cable Modem system. To analyze other system's logs, need port several application dependent files as following:
logparser/preporcess_cm.py
logparser/drain2_cm.py
oldschool/knowledgebase_cm.py

## **Running Environment**

**# Python version**

3.6 or above

**# Basics packages**

pip install --upgrade numpy scipy scikit-learn pandas matplotlib tqdm skl2onnx onnxruntime

**# PyTorch**

see https://pytorch.org/ for install instructions. The version is 1.5.0 or above.

