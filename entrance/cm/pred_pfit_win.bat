@echo off

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=MultinomialNB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Extract the label vector from norm file
python ..\..\logparser\extractlabels.py

rem Parse the log and generate templates ...
python ..\..\logparser\cm\parser.py

rem The machine learning way to analyze log data
python ..\..\detector\supervised_learning_pred.py

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=Perceptron
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt
python ..\..\detector\supervised_learning_pred.py

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_SVM
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt
python ..\..\detector\supervised_learning_pred.py

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_LR
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt
python ..\..\detector\supervised_learning_pred.py
