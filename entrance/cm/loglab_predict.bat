@echo off

rem This script predicts using the model of Loglab

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=LOGLAB
echo WINDOW_SIZE=10
echo WINDOW_STEP=1
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem logs/raw/cm/loglab/c001/ ... /cxxx/
copy ..\..\logs\raw\cm\loglab\c001\loglab_rfcut_ds_us_001.txt ..\..\logs\cm\test.txt

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py

rem Train the model of Loglab
python ..\..\loglab\loglab_model_pred.py
