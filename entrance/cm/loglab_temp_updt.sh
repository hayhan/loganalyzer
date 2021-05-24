#! /bin/bash

# This script updates the template library by the logs for Loglab

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=0
echo MODEL=LOGLAB
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# Concatenate multiple raw files into one by reading logs under
# logs/raw/cm/loglab/c001/ ... /cxxx/
python3 ../../tools/cat_files_across.py

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Extract sample info
python3 ../../logparser/extract_samples.py

# Parse the log and update the template library
python3 ../../logparser/cm/parser.py
