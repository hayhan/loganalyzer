@echo off

rem This script updates the template library

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=0
echo MODEL=TEMPUPDT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Concatenate all the log files under logs/raw/cm/ and store it as logs/cm/train.txt
python ..\..\logparser\cat_files.py logs/raw/cm

rem Insert temp_updt_manu.txt to the head of train.txt
rem Do not use unix cat command because of trailing ^M char.
copy ..\..\logs\raw\cm\others\temp_updt_manu.txt ..\..\logs\cm\tmp1.txt > nul
ren ..\..\logs\cm\train.txt tmp2.txt

set fileList=tmp1.txt/tmp2.txt
python ..\..\logparser\cat_files.py logs/cm %fileList%
del ..\..\logs\cm\tmp*.txt

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Remove labels in logs if any
python ..\..\logparser\extract_labels.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py
