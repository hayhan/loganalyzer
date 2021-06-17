@echo off

rem This script normalizes the timestamp of logs. And then used for
rem DeepLog, Loglab training and template lib update

rem Configure parameters for logparser
rem TRAINING=0; METRICS=0; MODEL=DEEPLOG, LOGLAG OR OSS
rem Same parameters as DeepLog/Loglab prediction and OSS
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=LOGLAB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Iterate each file under logs/tmp/, detect the width of old
rem timestamp and replace old one with the standard format we defined
python ..\..\logparser\norm_timestamp.py
