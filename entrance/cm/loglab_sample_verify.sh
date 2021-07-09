#! /bin/bash

# This script updates the template library by the logs for Loglab

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=LOGLAB.RFC
echo WINDOW_SIZE=10
echo WINDOW_STEP=1
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# logs/raw/cm/loglab/c001/ ... /cxxx/
cp ../../logs/raw/cm/loglab/c009/loglab_psv_us_010.txt ../../logs/cm/test.txt

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Parse the log and update the template library
python3 ../../logparser/cm/parser.py

# Verify the typical features and the ones within the window
python3 ../../loglab/typical_features_verify.py
