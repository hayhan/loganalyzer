# **Log Analyzer**

## **Usage**

### Raw log format prerequisite
Add timestamp like this one "[20190719-08:58:23.748] " at the start of each line. This not always necessary as we support arbitrary timestamp format including no timestamp for prediction of Loglab, DeepLog and OSS (Old School System) now. Loglizer always needs this standard timestamp.

### Label your training logs
Put a string "abn: " after the timestamp for the anomaly log. If it is a multi-line log, we just label the first line. The labeling is needed for Loglizer but not for the training and predition of Loglab, DeepLog, and OSS. While for validation purpose, the labeling is needed in DeepLog.

### Train / Validate the model

**# Loglizer**

1) copy the labeled training/validation log files to data/raw/LOG_TYPE/labeled/. Change the file list in train.lst and validate.lst.
2) run "analyzer loglizer train" or "analyzer loglizer validate"
3) parameters can be changed in config file, e.g. select different model, window size, etc. run "analyzer config show/edit/..."

**# DeepLog**

1) put the training/validation log files to data/raw/LOG_TYPE/normal/
2) run "analyzer loglizer train/validate"

**# Loglab**

1) put the training log files (already classified) to data/raw/LOG_TYPE/loglab/
2) run "analyzer loglab train"

### Prediction

**# Loglizer**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer loglizer predict"
3) anomalies are save to data/test/LOG_TYPE/results_loglizer.csv

**# DeepLog**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer deeplog predict"
3) anomalies are save to data/test/LOG_TYPE/results_deeplog.txt

**# Loglab**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer loglab predict"
3) anomalies are save to data/test/LOG_TYPE/results_loglab.txt

**# Old School System (OSS)**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer oldschool run"
3) results are save to data/test/LOG_TYPE/analysis_summary.csv and analysis_summary_top.txt.

## **Porting to Other Log Producing Systems**

LOG_TYPE currently supports 'cm' only. To analyze other system's logs, we need port application dependent files in new LOG_TYPE folders:

analyzer/preprocess/LOG_TYPE/
analyzer/parser/LOG_TYPE/
analyzer/oldschool/LOG_TYPE/

## **Running Environment**

**# Python version**

3.6 or above

**# Basics packages**

pip install --upgrade numpy scipy scikit-learn pandas matplotlib tqdm skl2onnx onnxruntime

**# PyTorch**

see https://pytorch.org/ for install instructions. The version is 1.5.0 or above.

**# Installation**

At the top directory of loganalyzer clone, run command below to install the analyzer package. Then you can use the "analyzer" command. Type "analyzer --help" for sub commands and options.

pip install .

To generate html api documents, run command below under docs directory:

make html
