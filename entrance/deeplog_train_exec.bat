@echo off

rem This script train the DeepLog exec model

rem ---Concatenate multiple raw files into one
rem ---Parameters: script inputLoc filenames outputLoc
set fileList=log_4_3390.txt/^
normal_0_register_202.txt/normal_1_register_202.txt/normal_2_dbc_202.txt/normal_3.txt/^
temp_updt_bfm_a350.txt/temp_updt_bfm_a351.txt/temp_updt_bfm_a370.txt/^
temp_updt_bfm_a375.txt/temp_updt_bfm_a380.txt/temp_updt_bfm_a383.txt/^
temp_updt_bfm_b329.txt/temp_updt_bfm_b330.txt/temp_updt_bfm_b331.txt/^
temp_updt_bfm_b400.txt/temp_updt_bfm_b405.txt/temp_updt_bfm_b415.txt

rem Concatenate above files into one and add segment sign 'segsign: '
python ..\tools\cat_files_sign.py logs/raw %fileList% logs/train.txt

(
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

rem Preprocess
python ..\logparser\preprocess_cm.py

rem Save the segment size to a vector and remove them from norm file 
python ..\logparser\extractseg.py

rem Parse the log and update the template library
python ..\logparser\drain2_cm.py

rem Train the model
(
echo TRAINING=1
echo METRICS=1
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

python ..\deeplog\exec_path_anomaly_train.py
