#! /bin/bash

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=MultinomialNB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Extract the label vector from norm file
python3 ../../logparser/extract_labels.py

# Parse the log and generate templates ...
python3 ../../logparser/cm/parser.py

# The machine learning way to analyze log data
python3 ../../detector/supervised_learning_pred.py

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=Perceptron
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
python3 ../../detector/supervised_learning_pred.py

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_SVM
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
python3 ../../detector/supervised_learning_pred.py

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_LR
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
python3 ../../detector/supervised_learning_pred.py
