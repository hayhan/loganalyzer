@echo off

rem ---Process train dataset
(
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
rem ---Preprocess
python ..\logparser\preprocess_cm.py
rem Extract the label vector from norm file
python ..\logparser\extractlabels.py
rem ---Parse the log and generate templates ...
python ..\logparser\drain2_cm.py

rem ---Process test dataset
(
echo TRAINING=0
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\logparser\preprocess_cm.py
rem Extract the label vector from norm file
python ..\logparser\extractlabels.py
rem ---Parse the log and generate templates ...
python ..\logparser\drain2_cm.py

rem ---Train and test on different models
python ..\detector\supervised_learning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=LR
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\detector\supervised_learning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=SVM
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\detector\supervised_learning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=RFC
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\detector\supervised_learning_train.py
