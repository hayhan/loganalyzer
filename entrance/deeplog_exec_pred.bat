@echo off

rem This script does prediction using the DeepLog exec model

rem Adapt boardfarm CM logs
rem python ..\adapter\boardfarm_cm.py

rem copy ..\logs\raw\temp_updt_bfm_a350.txt ..\logs\test.txt > nul

rem Configure parameters for logparser
(
echo TRAINING=0
echo METRICS=0
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

rem Preprocess
python ..\logparser\preprocess_cm.py

rem Parse the log and extract the templates
python ..\logparser\drain2_cm.py

rem Configure parameters for DeepLog exec model
(
echo TRAINING=0
echo METRICS=0
echo MODEL=EXEC
echo WINDOW_SIZE=10
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=100
echo NUM_WORKERS=0
echo HIDDEN_SIZE=256
echo TOPK=10
echo DEVICE=cpu
) > deeplog_config.txt

rem Do prediction using DeepLog exec model
python ..\deeplog\exec_path_anomaly_pred.py
