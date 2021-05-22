#! /bin/bash

# This script trains the model of Loglab

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=LOGLAB
echo WINDOW_SIZE=10
echo WINDOW_STEP=1
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# logs/raw/cm/loglab/c001/ ... /cxxx/
cp ../../logs/raw/cm/loglab/c001/loglab_rfcut_ds_us_001.txt ../../logs/cm/test.txt

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Parse the log and update the template library
python3 ../../logparser/cm/parser.py

# Train the model of Loglab
python3 ../../loglab/loglab_model_pred.py