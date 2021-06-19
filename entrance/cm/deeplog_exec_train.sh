#! /bin/bash

# This script trains the DeepLog exec model

#--------------------------------------------------------------------
# Train dataset
#--------------------------------------------------------------------

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# Concatenate files under logs/raw/cm/normal into one and add session label 'segsign: '
python3 ../../logparser/cat_files.py logs/raw/cm/normal

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Do not consider abnormal label in train dataset for DeepLog as we suppose all the
# logs in train dataset are normal, say, DeepLog is unsupervised.

# Save the session size to a vector, then remove the session labels from norm file 
python3 ../../logparser/segment_info.py

# Parse the log and update the template library
python3 ../../logparser/cm/parser.py

#--------------------------------------------------------------------
# Test dataset for validation
#--------------------------------------------------------------------

cp ../../logs/raw/cm/labeled/log_2_3390_labeled.txt ../../logs/cm/test.txt

(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=1
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# Preprocess
python3 ../../logparser/cm/preprocess.py

# We need firstly extract abnormal labels, then extract session vector
# Do NOT reverse them.

# Extract the abnormal labels from norm file
python3 ../../logparser/extract_labels.py

# Save the session size to a vector, then remove the session labels from norm file 
python3 ../../logparser/segment_info.py

# Parse the log and extract the templates
python3 ../../logparser/cm/parser.py

#--------------------------------------------------------------------
# Train the DeepLog exec model, then do a validation
#--------------------------------------------------------------------

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=10
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=150
echo NUM_WORKERS=0
echo HIDDEN_SIZE=128
echo TOPK=10
echo DEVICE=cpu
echo NUM_DIR=1
) > ../deeplog_config.txt

python3 ../../deeplog/exec_path_anomaly_train.py

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=15
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=150
echo NUM_WORKERS=0
echo HIDDEN_SIZE=128
echo TOPK=10
echo DEVICE=cpu
echo NUM_DIR=1
) > ../deeplog_config.txt

python3 ../../deeplog/exec_path_anomaly_train.py
