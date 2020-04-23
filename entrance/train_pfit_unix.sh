#! /bin/bash

# Process train dataset
(
echo TRAINING=1
echo METRICS=1
echo MODEL=MultinomialNB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
# Preprocess and label raw log
python3 ../logparser/preprocess_CM.py
# Parse the log and generate templates ...
python3 ../logparser/Drain2_CM.py

# Process test dataset
(
echo TRAINING=0
echo METRICS=1
echo MODEL=MultinomialNB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python3 ../logparser/preprocess_CM.py
# Parse the log and generate templates ...
python3 ../logparser/Drain2_CM.py

# Train and test on different models
python3 ../detector/SupervisedLearning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=Perceptron
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python3 ../detector/SupervisedLearning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_SVM
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python3 ../detector/SupervisedLearning_train.py

(
echo TRAINING=0
echo METRICS=1
echo MODEL=SGDC_LR
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python3 ../detector/SupervisedLearning_train.py