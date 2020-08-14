@echo off

rem This script updates the template library

rem ---Concatenate multiple raw files into one
rem ---Parameters: script inputLoc filenames outputLoc
rem set fileList=log_0_3390.txt/log_2_3390.txt/log_3_3390.txt/log_4_3390.txt/^
rem normal_0_register_202.txt/normal_1_register_202.txt/normal_2_dbc_202.txt/^
rem normal_3.txt/temp_updt_0.txt

rem python ..\tools\cat_files.py logs/raw %fileList% logs/train.txt

(
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

rem Separately process temp_updt_1.txt to workaround the Drain initial sim issue
rem copy ..\logs\raw\temp_updt_1.txt ..\logs\train.txt > nul
rem copy ..\logs\raw\temp_updt_bfm_a383.txt ..\logs\train.txt > nul
rem copy ..\logs\raw\temp_updt_bfm_a350.txt ..\logs\train.txt > nul
rem copy ..\logs\raw\temp_updt_manu.txt ..\logs\train.txt > nul

rem Preprocess
python ..\logparser\preprocess_cm.py

rem Parse the log and update the template library
python ..\logparser\drain2_cm.py
