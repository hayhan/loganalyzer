@echo off

rem This script trains the DeepLog exec model

rem -----------------------------------------------------------------
rem Train dataset
rem -----------------------------------------------------------------

rem ---Concatenate multiple raw files into one
rem ---Parameters: script inputLoc filenames outputLoc
set fileList=normal_0_register_202.txt/^
normal_1_register_202.txt/normal_2_dbc_202.txt/normal_3.txt/^
temp_updt_bfm_a350.txt/temp_updt_bfm_a351.txt/temp_updt_bfm_a370.txt/^
temp_updt_bfm_a375.txt/temp_updt_bfm_a380.txt/temp_updt_bfm_a383.txt/^
temp_updt_bfm_a425.txt/^
temp_updt_bfm_b329.txt/temp_updt_bfm_b330.txt/temp_updt_bfm_b331.txt/^
temp_updt_bfm_b400.txt/temp_updt_bfm_b405.txt/temp_updt_bfm_b415.txt/^
temp_updt_bfm_b433.txt/temp_updt_bfm_b451.txt/^
normal_4_register_211.txt/normal_5_otf_mdd_ucd_211.txt/normal_6_dbc_211.txt/^
normal_7_no_ofdm_211.txt/normal_8_no_ofdma_211.txt/normal_9_voice_ipv4_211.txt/^
normal_10_voice_ipv4_211.txt

rem Concatenate above files into one and add session label 'segsign: '
python ..\..\tools\cat_files_sessions.py logs/raw/cm %fileList% logs/cm/train.txt

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Do not consider abnormal label in train dataset for DeepLog as we suppose all the
rem logs in train dataset are normal, say, DeepLog is unsupervised.

rem Save the session size to a vector, then remove the session labels from norm file
python ..\..\logparser\extractsessions.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py

rem -----------------------------------------------------------------
rem Test dataset for validation
rem -----------------------------------------------------------------

copy ..\..\logs\raw\cm\log_2_3390_labeled.txt ..\..\logs\cm\test.txt > nul

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem We need firstly extract abnormal labels, then extract session vector
rem Do NOT reverse them.

rem Extract the abnormal labels from norm file
python ..\..\logparser\extractlabels.py

rem Save the session size to a vector, then remove the session labels from norm file
python ..\..\logparser\extractsessions.py

rem Parse the log and extract the templates
python ..\..\logparser\cm\parser.py

rem -----------------------------------------------------------------
rem Train the DeepLog exec model, then do a validation
rem -----------------------------------------------------------------

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
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

python ..\..\deeplog\exec_path_anomaly_train.py

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=15
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=150
echo NUM_WORKERS=0
echo HIDDEN_SIZE=128
echo TOPK=10
echo DEVICE=cpu
echo NUM_DIR=1
) > ..\deeplog_config.txt

python ..\..\deeplog\exec_path_anomaly_train.py