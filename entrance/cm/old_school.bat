@echo off

(
echo TRAINING=0
echo METRICS=0
echo MODEL=OSS
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Adapt boardfarm CM logs
rem python ..\..\adapter\boardfarm_cm.py

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Parse the log and generate templates ...
python ..\..\logparser\cm\parser.py

rem The oldshool way to analyze log data
python ..\..\oldschool\analyzer.py
