#! /bin/bash

# This script updates the template library

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=0
echo MODEL=TEMPUPDT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

cp ../../logs/raw/cm/others/temp_updt_manu.txt ../../logs/cm/train.txt

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Remove labels in logs if any
python3 ../../logparser/extract_labels.py

# Parse the log and update the template library
python3 ../../logparser/cm/parser.py
