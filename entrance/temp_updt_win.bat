@echo off

rem This script updates the template library

(
echo TRAINING=1
echo METRICS=0
echo MODEL=TEMPUPDT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

rem ---Concatenate multiple raw files into one
rem ---Parameters: script inputLoc filenames outputLoc
rem set fileList=log_0_3390_labeled.txt/log_2_3390_labeled.txt/log_3_3390_labeled.txt/log_4_3390_labeled.txt/^
rem normal_0_register_202.txt/normal_1_register_202.txt/normal_2_dbc_202.txt/^
rem normal_3.txt/temp_updt_0.txt

rem python ..\tools\cat_files.py logs/raw %fileList% logs/train.txt

rem Preprocess
rem python ..\logparser\preprocess_cm.py

rem Remove labels in logs if any
rem python ..\logparser\extractlabels.py

rem Parse the log and update the template library
rem python ..\logparser\drain2_cm.py

rem Separately process temp_updt_1.txt to workaround the Drain initial sim issue
rem set fileList=temp_updt_1.txt/temp_updt_2.txt/temp_updt_manu.txt/^
rem temp_updt_bfm_a383.txt/temp_updt_bfm_a350.txt/temp_updt_bfm_a351.txt/temp_updt_bfm_a370.txt/^
rem temp_updt_bfm_a375.txt/temp_updt_bfm_a416.txt/temp_updt_bfm_a425.txt/temp_updt_bfm_b329.txt/^
rem temp_updt_bfm_b330.txt/temp_updt_bfm_b331.txt/temp_updt_bfm_b400.txt/temp_updt_bfm_b405.txt/^
rem temp_updt_bfm_b415.txt/temp_updt_bfm_b451.txt/^
rem normal_4_register_211.txt/normal_5_otf_mdd_ucd_211.txt/normal_6_dbc_211.txt/normal_7_no_ofdm_211.txt/^
rem normal_8_no_ofdma_211.txt/^
rem abnormal_1_diplexer_211.txt/abnormal_2_t4_211.txt/^
rem temp_updt_manu.txt

rem python ..\tools\cat_files.py logs/raw %fileList% logs/train.txt

copy ..\logs\raw\temp_updt_manu.txt ..\logs\train.txt > nul

rem Preprocess
python ..\logparser\preprocess_cm.py

rem Remove labels in logs if any
python ..\logparser\extractlabels.py

rem Parse the log and update the template library
python ..\logparser\drain2_cm.py
