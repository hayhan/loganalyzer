#! /bin/bash

# This script normalizes the timestamp of logs. And then used for
# DeepLog, Loglab training and template lib update

# Configure parameters for logparser
# TRAINING=0; METRICS=0; MODEL=DEEPLOG, LOGLAG OR OSS
# Same parameters as DeepLog/Loglab prediction and OSS
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=LOGLAB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# Iterate each file under logs/tmp/, detect the width of old
# timestamp and replace old one with the standard format we defined
python3 ../../logparser/norm_timestamp.py
