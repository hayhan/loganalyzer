#! /bin/bash

# Concatenate multiple raw files into one
# Parameters: script inputLoc filenames outputLoc
fileList="log_0_3390_labeled.txt/log_2_3390_labeled.txt\
/log_3_3390_labeled.txt/log_4_3390_labeled.txt"
python3 ../../tools/cat_files.py logs/raw/cm ${fileList} logs/cm/train.txt

cp ../../logs/raw/cm/log_2_3390_labeled.txt ../../logs/cm/test.txt
./train_static_unix.sh
cp ../../logs/raw/cm/log_1_3390_labeled.txt ../../logs/cm/test.txt
./pred_static_unix.sh
