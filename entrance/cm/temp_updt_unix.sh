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

# Concatenate all the log files under logs/raw/cm/ and store it as logs/cm/train.txt
python3 ../../logparser/cat_files.py logs/raw/cm

# Insert temp_updt_manu.txt to the head of generated train.txt to workaround some
# similarity threshold issue in Drain agorithm
# Do not use unix cat command because of the trailing ^M char.
cp ../../logs/raw/cm/others/temp_updt_manu.txt ../../logs/cm/tmp1.txt
mv ../../logs/cm/train.txt ../../logs/cm/tmp2.txt

fileList="tmp1.txt/tmp2.txt"
python3 ../../logparser/cat_files.py logs/cm ${fileList}
rm ../../logs/cm/tmp*.txt

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Remove labels in logs if any
python3 ../../logparser/extract_labels.py

# Parse the log and update the template library
python3 ../../logparser/cm/parser.py
