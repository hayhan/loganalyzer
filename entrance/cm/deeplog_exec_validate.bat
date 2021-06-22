@echo off

rem This script validates the DeepLog exec model

rem -----------------------------------------------------------------
rem Test dataset for validation
rem -----------------------------------------------------------------

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Concatenate files under logs/raw/cm/normal into one and add session label 'segsign: '
python ..\..\logparser\cat_files.py logs/raw/cm/normal

rem copy ..\..\logs\raw\cm\labeled\log_2_3390_labeled.txt ..\..\logs\cm\test.txt > nul

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem We need firstly extract abnormal labels, then extract session vector
rem Do NOT reverse them.

rem Extract the abnormal labels from norm file
python ..\..\logparser\extract_labels.py

rem Save the session size to a vector, then remove the session labels from norm file
python ..\..\logparser\segment_info.py

rem Parse the log and extract the templates
python ..\..\logparser\cm\parser.py

rem -----------------------------------------------------------------
rem Do a validation
rem -----------------------------------------------------------------

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=10
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=100
echo NUM_WORKERS=0
echo HIDDEN_SIZE=128
echo TOPK=10
echo DEVICE=cpu
echo NUM_DIR=1
) > ..\deeplog_config.txt

python ..\..\deeplog\exec_path_anomaly_validate.py

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=15
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=100
echo NUM_WORKERS=0
echo HIDDEN_SIZE=128
echo TOPK=10
echo DEVICE=cpu
echo NUM_DIR=1
) > ..\deeplog_config.txt

python ..\..\deeplog\exec_path_anomaly_validate.py
