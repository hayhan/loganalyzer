#! /bin/bash

# Get the absolute path of current shell script
SHELL_FOLDER=$(dirname $(readlink -f "$0"))

# Set the python virtual enviroment
source $SHELL_FOLDER/../../pyVirtEnvs/log_env/bin/activate

# Set parameters for loganalyzer
(
echo TRAINING=0
echo METRICS=0
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

# Adapt boardfarm CM logs
#python3 $SHELL_FOLDER/../adapter/boardfarm_cm.py

# Preprocess
python3 $SHELL_FOLDER/../logparser/preprocess_cm.py

# Extract the label vector from norm file
python3 $SHELL_FOLDER/../logparser/extractlabels.py

# Parse the log and generate templates ...
python3 $SHELL_FOLDER/../logparser/drain2_cm.py

# The machine learning way to analyze log data
#python3 $SHELL_FOLDER/../detector/supervised_learning_pred.py
# The oldshool way to analyze log data
python3 $SHELL_FOLDER/../oldschool/analyzer.py

