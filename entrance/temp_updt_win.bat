@echo off
setlocal EnableDelayedExpansion

rem This script updates the template library

rem ---Concatenate multiple raw files into one
rem ---parameters: script inputLoc filenames outputLoc
rem ---format: !="!^ is used for spliting a long string
rem set fileList="normal_0_register_202.txt/normal_1_register_202.txt/!="!^
rem temp_updt_0.txt/temp_updt_1.txt"

rem python ..\tools\cat_files.py logs/raw %fileList% logs/train.txt

(
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

copy ..\logs\raw\normal_2_dbc_202.txt ..\logs\train.txt > nul

rem Preprocess
python ..\logparser\preprocess_cm.py

rem Parse the log and update the template library
python ..\logparser\drain2_cm.py
