@echo off

(
echo TRAINING=0
echo MODEL=MultinomialNB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

rem Preprocess and label raw log if validation needed
python ..\logparser\logpurger.py

rem Parse the log and generate templates ...
python ..\logparser\Drain2_DOCSIS_demo.py

rem The machine learning way to analyze log data
python ..\detector\demo\SupervisedLearning_pred.py
rem The oldshool way to analyze log data
python ..\oldschool\analyzer.py