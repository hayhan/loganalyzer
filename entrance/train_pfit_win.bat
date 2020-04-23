@echo off

rem ---Process train dataset
(
echo TRAINING=1
echo METRICS=1
echo MODEL=MultinomialNB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
rem ---Preprocess and label raw log
python ..\logparser\preprocess_CM.py
rem ---Parse the log and generate templates ...
python ..\logparser\Drain2_CM.py

rem ---Process test dataset
(
echo TRAINING=0
echo METRICS=1
echo MODEL=MultinomialNB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\logparser\preprocess_CM.py
rem ---Parse the log and generate templates ...
python ..\logparser\Drain2_CM.py

rem ---Train and test on different models
python ..\detector\SupervisedLearning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=Perceptron
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\detector\SupervisedLearning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_SVM
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\detector\SupervisedLearning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_LR
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python ..\detector\SupervisedLearning_train.py