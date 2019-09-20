@echo off

rem ---Process train dataset
echo TRAINING=1 > config.txt
rem ---Preprocess and label raw log
python ..\logparser\logpurger.py
python ..\logparser\labelprocess.py
rem ---Parse the log and generate templates ...
python ..\logparser\Drain_DOCSIS_demo.py

rem ---Process test dataset
echo TRAINING=0 > config.txt
python ..\logparser\logpurger.py
python ..\logparser\labelprocess.py
rem ---Parse the log and generate templates ...
python ..\logparser\Drain_DOCSIS_demo.py

rem ---Train and test on different models
python ..\detector\demo\DecisionTree_demo.py
python ..\detector\demo\LR_demo.py
python ..\detector\demo\SVM_demo.py