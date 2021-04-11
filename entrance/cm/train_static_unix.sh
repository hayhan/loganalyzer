#! /bin/bash

# Process train dataset
(
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
# Preprocess
python3 ../../logparser/cm/preprocess.py
# Extract the label vector from norm file
python3 ../../logparser/extractlabels.py
# Parse the log and generate templates ...
python3 ../../logparser/cm/parser.py

# Process test dataset
(
echo TRAINING=0
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
python3 ../../logparser/cm/preprocess.py
# Extract the label vector from norm file
python3 ../../logparser/extractlabels.py
# Parse the log and generate templates ...
python3 ../../logparser/cm/parser.py

# Train and test on different models
python3 ../../detector/supervised_learning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=LR
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
python3 ../../detector/supervised_learning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=SVM
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
python3 ../../detector/supervised_learning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=RFC
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt
python3 ../../detector/supervised_learning_train.py
