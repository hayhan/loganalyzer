#! /bin/bash

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# Concatenate multiple raw files into one
# Parameters: script inputLoc filenames
# Note: Detector needs monotonic increasing timestamp, so manually list files
# and cat them in sequence.
fileList="log_0_3390_labeled.txt/log_2_3390_labeled.txt\
/log_3_3390_labeled.txt/log_4_3390_labeled.txt"
python3 ../../logparser/cat_files.py logs/raw/cm/labeled ${fileList}

cp ../../logs/raw/cm/labeled/log_2_3390_labeled.txt ../../logs/cm/test.txt
./train_static_unix.sh
cp ../../logs/raw/cm/others/log_1_3390_labeled.txt ../../logs/cm/test.txt
./pred_static_unix.sh
