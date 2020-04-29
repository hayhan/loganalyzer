#! /bin/bash

# Concatenate multiple raw files into one
# parameters: script inputLoc filenames outputLoc
fileList="log_0_3390_labeled.txt/log_2_3390_labeled.txt\
/log_3_3390_labeled.txt/log_4_3390_labeled.txt"
python3 ../tools/cat_files.py logs/raw ${fileList} logs/train.txt

cp ../logs/raw/log_2_3390_labeled.txt ../logs/test.txt
./train_static_unix.sh
cp ../logs/raw/log_1_3390_labeled.txt ../logs/test.txt
./pred_static_unix.sh