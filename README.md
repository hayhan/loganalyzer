# **LogAnalyzer**

*LogAnalyzer* is a platform for various system/app log parsing and analyzing. It includes pre-processor, parser, analyzer and post-processor. The analyzer supports [Loglab][link1] for multi-classification of issues, [Loglizer][link2] and [DeepLog][link3] for anomaly detection (aka. binary classification). For multi-classification of logs, it only needs few log samples of each category for training as we make use of domain knowledgebase in the process of feature extraction.

![Loglab Overview](/tmp/loglab_overview.png 'Loglab Overview')

Unlike most of the existing apps of log analyzing that only handle standard format logs (e.g. syslog), *LogAnalyzer* accepts logs of free style format. E.g. It doesn't require severity fields, and even timestamp for Loglab and DeepLog. It permits embedded multi-lines (aka. indented lines block), tables, etc. The pre-processor will normalize the logs of free style format to standard one.

It also includes some amazing capabilities for raw log parsing like learning of timestamp width and recovering of entangled / broken lines because of multi-thread printing to same stdout console.

The platform supports CLI commands / portable APIs to do most of the works including data washing, pre-processing, parsing, training, predicting, debugging and can be easily ported to embedded devices for inference.

## **Usage**

We take the logs from ftp app FileZilla client as example to show how to pre-process, parse, build knowledge base, extract features, train and predict. We suppose you already setup the running enviroment otherwise check out the section of [Running Environment](#running-environment) at the end of the doc.

### Prepare data set
First, extract the *data/raw.7z* to *data/*. The *data/raw/ftp/loglab/* contains log samples in categories (c001/c002/c003) that are used to train Loglab. The *data/raw/ftp/labeled/* contains labeled (string 'abn: ' indicates abnormal) logs that are used to train Loglizer as well as to validate DeepLog. The *data/raw/ftp/normal/* contains normal logs that are used to train DeepLog. The *data/raw/ftp/abnormal/* contrains logs that are used for inference. The *data/raw/ftp/others/* contains some logs for special purposes.

### Configure *LogAnalyzer*
There is a top level configuration file *analyzer/config/config.yaml* where you can set parameters for each module. The first thing to configure is to set the item "general: log_type" to the type you are handling. Here we set "ftp" as we take it as the example. Besides the top level one, there is an override version of it called config_overwrite.yaml in *data/persist/ftp/*. It is a sub-set of the top level one. The system loads the based config firstly and then update the in-memory contents with the override one.

Console command "*\$ analyzer config*" shows the help info for configuration. "*\$ analyzer config updt --item general log_type ftp*" changes the LOG_TYPE to yours.

### Build the log template library
Template library is the base of the whole system. It is saved in *data/persist/LOG_TYPE/template_lib.csv*. In our example, LOG_TYPE is *ftp*. Take notice that, this directory is empty initially when you start to add support for your LOG_TYPE logs.

Console command "*\$ analyzer template*" shows the help info. "*\$ analyzer template updt*" creates and updates the library using all the logs under *data/raw/LOG_TYPE/*.

Take notice that, the library build/update command does pre-processing for raw logs in advance. The train command that we will introduce does the pre-processing and lib updating firstly too. The predict command does the similar thing as train except that it only creates templates and doesn't update the library.

### Multi-classification of logs with [Loglab][link1]
Now we are going to train the model for multi-classification of issues. Before running the train command, we need prepare something for the feature extraction.

Still take logs from FileZilla client as example. Collect some abnormal logs and categorize them into 3 classes, aka. c001: upload fails because of no write access, c002: login fails because of wrong usr name / password, c003: login fails because of TLS.

In the section of [Prepare data set](#prepare-data-set), we put the logs to *data/raw/ftp/loglab/* in a way of a sample per file. A sample is a collection of logs that include a sub-set of typical logs. These typical logs represent a kind of failure exclusively. In a nutshell, we use the set of typical logs (aka. typical templates after parsing) together with the contexts as the feature for classificaiton.

The *data/persist/ftp/classes_loglab.yaml* contains category info for the multi-classification. The *data/persist/ftp/kb_no_para.yaml* contains typical templates whose parameters we don't care. The *analyzer/extensions/ftp/knowledgebase.py* contains typical templates whose parameters we care. The *data/persist/ftp/exec_para_loglab.yaml* contains parameters for the feature extraction.

Now let's train the models for multi-classification and visualize the result as following:

Console command "*\$ analyzer loglab*" shows the help info for multi-classification. "*\$ analyzer loglab train*" trains the model with RFC (Random Forrest). "*\$ analyzer loglab show*" displays the supported models. "*\$ analyzer loglab train --debug*" saves the event matrix to the disk, and then we can use "*\$ analyzer utils viz --src train ecm_loglab.txt --label*" to visualize the classification.

To predict with the just trained model, copy the tested raw log file to *data/cooked/LOG_TYPE/test.txt* (LOG_TYPE is ftp in our example). Then run "*\$ analyzer loglab predict*". The reports for the result are *data/test/LOG_TYPE/analysis_summary.csv* and *analysis_summary_top.txt*.

### Binary classification of logs (aka. Anomaly detection) with [Loglizer][link2] or [DeepLog][link3]
Besides multi-classification of issues, *LogAnalyzer* also support anomaly detection.

<span style="text-decoration:underline">[Loglizer][link2]:</span>

The Loglizer uses labeled logs for training. Still taking the ftp logs as example, we store the labeled logs under *data/raw/ftp/labeled/* (see section of [Prepare data set](#prepare-data-set)). Checkout the log example in that folder to see how the label "abn: " is inserted to the logs. Also checkout the files *data/persist/ftp/config_overwrite.yaml* and *data/persist/ftp/exec_para_loglizer.yaml*.

Then we can train, validate and predict using Loglizer console commands as following:

Console command "*\$ analyzer loglizer*" shows the help info. "*\$ analyzer loglizer show*" displays the supported models. "*\$ analyzer loglizer train*" trains the model with Decesion Tree by default. "*\$ analyzer loglizer train --model ALL*" trains all the static models of supported. "*\$ analyzer loglizer train --model ALL --inc*" trains all partial fit models (aka. incremental training) of supported. "*\$ analyzer loglizer validate --src labeled*" validates the models using the logs under *data/raw/ftp/labeled/*.

To predict with the just trained model, copy the tested raw log file to *data/cooked/LOG_TYPE/test.txt*. and then run "*\$ analyzer loglab predict*". The report for the result is *data/test/LOG_TYPE/results_loglizer.csv*. (LOG_TYPE is ftp in our example).

<span style="text-decoration:underline">[DeepLog][link3]:</span>

The DeepLog uses normal logs (*/data/raw/ftp/normal/*) for training. Checkout the *data/persist/ftp/config_overwrite.yaml* and *data/persist/ftp/exec_para_deeplog.yaml*. We implement exec model of DeepLog using PyTorch and make use of knowledge base (*analyzer/extensions/ftp/knowledgebase.py*) to implement the param model of DeepLog.

Console command "*\$ analyzer deeplog*" shows the help info. "*\$ analyzer deeplog train*" trains the model. "*\$ analyzer deeplog validate --src labeled*" validates the model using logs under *data/raw/ftp/labeled/*.

To predict with the just trained model, copy the tested raw log file to *data/cooked/LOG_TYPE/test.txt*. Then run "*\$ analyzer deeplog predict*". The report for the result is *data/test/LOG_TYPE/results_deeplog.txt*. (LOG_TYPE is ftp in our example).

Take notice that, the number of ftp logs is quite few for training of Loglizer and DeepLog, so the validation and prediction results are not so good. It is expected. We only take the ftp logs as example to show the usage and the method of porting. They have good results of prediction on our data set of CM logs, which is big enough.

## **Porting to Other Log Producing Systems**

LOG_TYPE currently supports 'cm' and 'ftp'. The former one indicates logs of DOCSIS from Cable Modem. The latter indicates logs from ftp app Filezilla client. To analyze other system's logs, you need to port application dependent files in the folder: *analyzer/extensions/LOG_TYPE/*. Also, make sure the correct LOG_TYPE is set in the config file: *analyzer/config/config.yaml*.

If your LOG_TYPE logs have very rich formats, e.g. containing tables, embedded multi-lines, etc., you may need to spend some efforts on implementing the *Preprocess::process_for_domain()* in *analyzer/extensions/LOG_TYPE/preprocess.py*. Please refer to the implementation of LOG_TYPE of cm for rich format logs preprocessing.

Take notice that the raw cm training logs are removed from the *data/raw.7z* in github repo because of proprietary.

## **Miscellaneous**

**About timestamp**

The timestamp is not necessary for Loglab and DeepLog except Loglizer. But for training of Loglab and DeepLog, we still feed *fake* timestamps to our app for being back compatible with Loglizer. If you have inconsistent format of timestamp for your logs, you can copy your logs to *data/tmp/* and then run "*\$ analyzer utils normts*" to normalize them. Take notice that it is only for training of Loglab and DeepLog. It always requires consistent format of timestamp for training and prediction of Loglizer.

**Timestamp width learning**

For prediction of Loglab and DeepLog, the timestamp in logs is not necessary and any format is allowed if it exists. The *LogAnalyzer* can learn the width of timestamp, e.g. the "*\$ analyzer loglab predict*" and "*\$ analyzer deeplog predict*" learn the width by default. The option is "*--learn-ts/--no-learn-ts*". It doesn't require to know the format/width of timestamp in advance.

## **Running Environment**

Activate python virtual environment firstly and then run following commands.

**Python version**

3.6 or above

**Basics packages**

*\$ pip install --upgrade numpy scipy scikit-learn pandas matplotlib tqdm skl2onnx onnxruntime pyyaml click sphinx pytest pytest-benchmark umap-learn*

Following packages are optional (for good experience of programing):
*pep8 autopep8 pylint flake8*

**PyTorch**

see https://pytorch.org/ for install instructions. The version is 1.5.0 or above. The DeepLog depends on it.

**Installation**

At the top directory of loganalyzer, run commands below (pay attention to the dot) to install the analyzer package. Then export environment var ANALYZER_DATA. Also, extract *raw.7z* to directory *data/*. Now you can use the "analyzer" command. Run "*\$ analyzer --help*" for sub commands and options.

*\$ pip install .*

[Linux or macOS]  
*\$ export ANALYZER_DATA=path_to_your_clone_dir/data*

[Windows PowerShell]  
*C:\\> $env:ANALYZER_DATA="path_to_your_clone_dir\data"*

To get api documents of html format, run commands below in *docs* directory of your clone. The generated html pages are under *docs/build/html/*.

[Linux or macOS]  
*\$ sphinx-apidoc -f -o source ../analyzer && make html*

[Windows PowerShell]  
*C:\\> sphinx-apidoc -f -o source ..\analyzer; .\make.bat html*

[link1]: https://hayhan.github.io/2023/01/29/loglab.html
[link2]: https://github.com/logpai/loglizer
[link3]: https://www.cs.utah.edu/~lifeifei/papers/deeplog.pdf
