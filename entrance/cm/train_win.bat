@echo off

rem ---Process train dataset
(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt
rem ---Preprocess
python ..\..\logparser\cm\preprocess.py
rem Extract the label vector from norm file
python ..\..\logparser\extractlabels.py
rem ---Parse the log and generate templates ...
python ..\..\logparser\cm\parser.py

rem ---Process test dataset
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt
python ..\..\logparser\cm\preprocess.py
rem Extract the label vector from norm file
python ..\..\logparser\extractlabels.py
rem ---Parse the log and generate templates ...
python ..\..\logparser\cm\parser.py

rem ---Train and test on different models
python ..\..\detector\supervised_learning_train.py
