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

copy ..\..\logs\raw\cm\others\temp_updt_manu.txt ..\..\logs\cm\train.txt > nul

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Remove labels in logs if any
python ..\..\logparser\extract_labels.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py
