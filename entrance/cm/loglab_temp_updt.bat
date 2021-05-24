@echo off

rem This script updates the template library by the logs for Loglab

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=0
echo MODEL=LOGLAB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Concatenate multiple raw files into one by reading logs under
rem logs/raw/cm/loglab/c001/ ... /cxxx/
python ..\..\tools\cat_files_across.py

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Extract sample info
python ..\..\logparser\extract_samples.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py
