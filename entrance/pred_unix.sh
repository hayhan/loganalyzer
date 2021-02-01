#! /bin/bash

(
echo TRAINING=0
echo METRICS=0
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

# Adapt boardfarm CM logs
#python3 ../adapter/boardfarm_cm.py

# Preprocess
python3 ../logparser/preprocess_cm.py

# Extract the label vector from norm file
python3 ../logparser/extractlabels.py

# Parse the log and generate templates ...
python3 ../logparser/drain2_cm.py

# The machine learning way to analyze log data
python3 ../detector/supervised_learning_pred.py
