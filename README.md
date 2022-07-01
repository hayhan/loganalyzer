# **Log Analyzer**

## **Usage**

### Raw log format prerequisite
Add timestamp like this one "[20190719-08:58:23.748] " at the start of each line. This not always necessary as we support arbitrary timestamp format including no timestamp for prediction of Loglab, DeepLog and OSS (Old School System) now. While Loglizer always needs this standard timestamp.

### Label your training logs
Put a string "abn: " after the timestamp for the anomaly log. If it is a multi-line log, we just label the first line. The labeling is needed for Loglizer but not for the training and prediction of Loglab, DeepLog, and OSS. While for validation purpose, the labeling is needed in DeepLog. For Loglab, we need classify the trianing log files into different groups with label "cxxx" as folder names. See examples in data/raw/cm/loglab or data/raw/ftp/loglab.

### Configuration files

Configuration files include a base one at analyzer/config/config.yaml and an overwrite version at data/persist/LOG_TYPE/config_overwrite.yaml, which is a sub-set of the former one. The system loads the based config firstly and then update the in-memory contents with the overwrite one.

### Train / Validate the model

**Loglizer**

1) put the labeled training or validation log files to data/raw/LOG_TYPE/labeled/. Change the file list in train.lst and validate.lst.
2) run "analyzer loglizer train" or "analyzer loglizer validate"

**DeepLog**

1) put the training or validation log files to data/raw/LOG_TYPE/normal/
2) run "analyzer deeplog train" or "analyzer deeplog validate"

**Loglab**

1) put the training log files (already classified) to data/raw/LOG_TYPE/loglab/
2) run "analyzer loglab train"

### Prediction

**Loglizer**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer loglizer predict"
3) anomalies are save to data/test/LOG_TYPE/results_loglizer.csv

**DeepLog**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer deeplog predict"
3) anomalies are save to data/test/LOG_TYPE/results_deeplog.txt

**Loglab**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer loglab predict"
3) results are save to data/test/LOG_TYPE/analysis_summary.csv and analysis_summary_top.txt.

**Old School System (OSS)**

1) copy the raw logs file to data/cooked/LOG_TYPE/test.txt.
2) run "analyzer oldschool run"
3) results are save to data/test/LOG_TYPE/analysis_summary.csv and analysis_summary_top.txt.

## **Porting to Other Log Producing Systems**

LOG_TYPE currently supports 'cm' and 'ftp'. The former one indicates logs of DOCSIS on Cable Modem. The latter indicates logs of ftp client of Filezilla. To analyze other system's logs, you need port application dependent files in the folder: analyzer/extensions/LOG_TYPE/. Also, make sure the correct LOG_TYPE is set in the config file: analyzer/config/config.yaml.

## **Running Environment**

Activate python virtual environment firstly and then run following commands.

**Python version**

3.6 or above

**Basics packages**

$ pip install --upgrade numpy scipy scikit-learn pandas matplotlib tqdm skl2onnx onnxruntime pyyaml click sphinx pytest pytest-benchmark umap-learn

*Following packages are optional:*
pep8 autopep8 pylint flake8

**PyTorch**

see https://pytorch.org/ for install instructions. The version is 1.5.0 or above. The DeepLog depends on it.

**Installation**

At the top directory of loganalyzer clone, run commands below (pay attention to the dot) to install the analyzer package. Then export environment var ANALYZER_DATA. Also, extract raw.7z in data. Now you can use the "analyzer" command. Type "analyzer --help" for sub commands and options.

$ pip install .

[Linux or macOS]
$ export ANALYZER_DATA=path_to_your_clone_dir/data

[Windows PowerShell]
C:\\> $env:ANALYZER_DATA="path_to_your_clone_dir\data"

To get api documents of html format, run commands below in docs directory of your clone. The generated html pages are under docs/build/html/.

[Linux or macOS]
$ sphinx-apidoc -f -o source ../analyzer && make html

[Windows PowerShell]
C:\\> sphinx-apidoc -f -o source ..\analyzer; .\make.bat html
