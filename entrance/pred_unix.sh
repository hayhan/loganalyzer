#! /bin/bash

(
echo TRAINING=0
echo METRICS=0
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

# Preprocess and label raw log if validation needed
python3 ../logparser/preprocess_CM.py

# Parse the log and generate templates ...
python3 ../logparser/Drain2_CM.py

# The machine learning way to analyze log data
python3 ../detector/SupervisedLearning_pred.py
# The oldshool way to analyze log data
python3 ../oldschool/analyzer.py