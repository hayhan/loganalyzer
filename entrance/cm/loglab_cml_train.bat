@echo off

rem This script predicts using the model of Loglab

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=0
echo MODEL=LOGLAB.RFC
echo WINDOW_SIZE=10
echo WINDOW_STEP=1
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Concatenate multiple raw files into one by reading logs under
rem logs/raw/cm/loglab/c001/ ... /cxxx/
python ..\..\logparser\cat_files.py logs/raw/cm/loglab

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Extract sample info
python ..\..\logparser\segment_info.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py

rem Train the model of Loglab
python ..\..\loglab\loglab_cml_train.py
