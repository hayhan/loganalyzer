#! /bin/bash

# This script train the DeepLog exec model

# Concatenate multiple raw files into one
# Parameters: script inputLoc filenames outputLoc
fileList="log_4_3390.txt\
normal_0_register_202.txt/normal_1_register_202.txt/normal_2_dbc_202.txt"

# Concatenate above files into one and add segment sign 'segsign: '
python3 ../tools/cat_files_sign.py logs/raw ${fileList} logs/train.txt

(
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

# Preprocess
python3 ../logparser/preprocess_cm.py

# Save the segment size to a vector and remove them from norm file 
python3 ../logparser/extractseg.py

# Parse the log and update the template library
python3 ../logparser/rain2_cm.py

# Train the model
(
echo TRAINING=1
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=10
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=100
echo NUM_WORKERS=0
echo HIDDEN_SIZE=256
echo TOPK=10
echo DEVICE=cpu
) > deeplog_config.txt

python3 ../deeplog/exec_path_anomaly_train.py
