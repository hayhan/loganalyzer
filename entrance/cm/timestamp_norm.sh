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

# Preprocess for detecting timestamp
python3 ../../logparser/cm/preprocess_ts.py

# Parse the log and generate templates for detecting timestamp
python3 ../../logparser/cm/parser.py

# Detect the timestamp
python3 ../../logparser/det_timestamp.py

# Replace customized timestamp with standard one we defined
python3 ../../logparser/fake_timestamp.py
