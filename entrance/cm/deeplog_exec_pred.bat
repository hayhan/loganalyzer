@echo off

rem This script does prediction using the DeepLog exec model

rem Adapt boardfarm CM logs
rem python ..\..\adapter\boardfarm_cm.py

rem copy ..\..\logs\raw\cm\temp_updt_bfm_b433.txt ..\..\logs\cm\test.txt > nul

rem Configure parameters for logparser
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Preprocess for detecting timestamp
python ..\..\logparser\cm\preprocess_ts.py

rem Parse the log and generate templates for detecting timestamp
python ..\..\logparser\cm\parser.py

rem Detect the timestamp
python ..\..\logparser\det_timestamp.py

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Parse the log and extract the templates
python ..\..\logparser\cm\parser.py

rem Postprocess to recover messed logs
python ..\..\logparser\cm\postprocess.py

rem The second time clustering for messed logs
python ..\..\logparser\cm\parser_again.py

rem Configure parameters for DeepLog exec model
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=EXEC
echo WINDOW_SIZE=10
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=150
echo NUM_WORKERS=0
echo HIDDEN_SIZE=128
echo TOPK=10
echo DEVICE=cpu
echo NUM_DIR=1
) > ..\deeplog_config.txt

rem Do prediction using DeepLog exec model
python ..\..\deeplog\exec_path_anomaly_pred.py
