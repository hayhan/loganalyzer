#! /bin/bash

# Process train dataset
(
echo TRAINING=1
echo MODEL=LR
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
# Preprocess and label raw log
python3 ../logparser/logpurger.py
python3 ../logparser/labelprocess.py
# Parse the log and generate templates ...
python3 ../logparser/Drain2_DOCSIS_demo.py

# Process test dataset
(
echo TRAINING=0
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt
python3 ../logparser/logpurger.py
python3 ../logparser/labelprocess.py
# Parse the log and generate templates ...
python3 ../logparser/Drain2_DOCSIS_demo.py

# Train and test on different models
python3 ../detector/demo/DecisionTree_demo.py
python3 ../detector/demo/LR_demo.py
python3 ../detector/demo/SVM_demo.py
