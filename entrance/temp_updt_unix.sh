#! /bin/bash

# This script updates the template library

# Concatenate multiple raw files into one
# Parameters: script inputLoc filenames outputLoc
#fileList="log_0_3390.txt/log_2_3390.txt/log_3_3390.txt/log_4_3390.txt/\
#normal_0_register_202.txt/normal_1_register_202.txt/normal_2_dbc_202.txt/\
#normal_3.txt/temp_updt_0.txt"

#python3 ../tools/cat_files.py logs/raw ${fileList} logs/train.txt

(
echo TRAINING=1
echo METRICS=1
echo MODEL=TEMPUPDT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

# Separately process temp_updt_1.txt to workaround the Drain initial sim issue
#cp ../logs/raw/temp_updt_1.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_2.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_a383.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_a350.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_a351.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_a370.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_a375.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_a380.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_b329.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_b330.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_b331.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_b400.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_b405.txt ../logs/train.txt
#cp ../logs/raw/temp_updt_bfm_b415.txt ../logs/train.txt
cp ../logs/raw/temp_updt_manu.txt ../logs/train.txt

# Preprocess
python3 ../logparser/preprocess_cm.py

# Parse the log and update the template library
python3 ../logparser/drain2_cm.py
