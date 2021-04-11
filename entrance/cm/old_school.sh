#! /bin/bash

# Get the absolute path of current shell script on Linux
# It is used on the Linux log web server
uname_out="$(uname -s)"
case "${uname_out}" in
    Linux*)    SHELL_FOLDER=$(dirname $(readlink -f "$0"));;
         *)    SHELL_FOLDER=./;;
esac

# Set the python virtual enviroment
source $SHELL_FOLDER/../../../pyVirtEnvs/log_env/bin/activate

# Set parameters for loganalyzer
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=OSS
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > $SHELL_FOLDER/../config.txt

# Adapt boardfarm CM logs
#python3 $SHELL_FOLDER/../../adapter/boardfarm_cm.py

# Detect timestamp
#python3 $SHELL_FOLDER/../../logparser/cm/preprocess_ts.py

# Parse the log and generate templates ...
#python3 $SHELL_FOLDER/../../logparser/cm/parser.py

# Preprocess
python3 $SHELL_FOLDER/../../logparser/cm/preprocess.py

# Parse the log and generate templates ...
python3 $SHELL_FOLDER/../../logparser/cm/parser.py

# The oldshool way to analyze log data
python3 $SHELL_FOLDER/../../oldschool/analyzer.py
