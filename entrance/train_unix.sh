#! /bin/bash

# Process train dataset
echo TRAINING=1 > config.txt
# Preprocess and label raw log
python ../logparser/logpurger.py
python ../logparser/labelprocess.py
# Parse the log and generate templates ...
python ../logparser/Drain_DOCSIS_demo.py

# Process test dataset
echo TRAINING=0 > config.txt
python ../logparser/logpurger.py
python ../logparser/labelprocess.py
# Parse the log and generate templates ...
python ../logparser/Drain_DOCSIS_demo.py

# Train and test on different models
python ../detector/demo/DecisionTree_demo.py
python ../detector/demo/LR_demo.py
python ../detector/demo/SVM_demo.py