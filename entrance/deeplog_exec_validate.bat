@echo off

rem This script validate the DeepLog exec model

rem -----------------------------------------------------------------
rem Test dataset for validation
rem -----------------------------------------------------------------

copy ..\logs\raw\log_2_3390_labeled.txt ..\logs\test.txt > nul

(
echo TRAINING=0
echo METRICS=1
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

rem Preprocess
python ..\logparser\preprocess_cm.py

rem We need firstly extract abnormal labels, then extract session vector
rem Do NOT reverse them.

rem Extract the abnormal labels from norm file
python ..\logparser\extractlabels.py

rem Save the session size to a vector, then remove the session labels from norm file
python ..\logparser\extractsessions.py

rem Parse the log and extract the templates
python ..\logparser\drain2_cm.py

rem -----------------------------------------------------------------
rem Do a validation
rem -----------------------------------------------------------------

(
echo TRAINING=0
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=10
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=10
echo NUM_WORKERS=0
echo HIDDEN_SIZE=256
echo TOPK=10
echo DEVICE=cpu
) > deeplog_config.txt

python ..\deeplog\exec_path_anomaly_validate.py
