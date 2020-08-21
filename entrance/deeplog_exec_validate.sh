#! /bin/bash

# This script validates the DeepLog exec model

#--------------------------------------------------------------------
# Test dataset for validation
#--------------------------------------------------------------------

cp ../logs/raw/log_2_3390_labeled.txt ../logs/test.txt

(
echo TRAINING=0
echo METRICS=1
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

# Preprocess
python3 ../logparser/preprocess_cm.py

# We need firstly extract abnormal labels, then extract session vector
# Do NOT reverse them.

# Extract the abnormal labels from norm file
python3 ../logparser/extractlabels.py

# Save the session size to a vector, then remove the session labels from norm file 
python3 ../logparser/extractsessions.py

# Parse the log and extract the templates
python3 ../logparser/drain2_cm.py

#--------------------------------------------------------------------
# Do a validation
#--------------------------------------------------------------------

(
echo TRAINING=0
echo METRICS=1
echo MODEL=EXEC
echo WINDOW_SIZE=10
echo TEMPLATE_LIB_SIZE=2000
echo BATCH_SIZE=32
echo NUM_EPOCHS=10
echo NUM_WORKERS=0
echo HIDDEN_SIZE=256
echo TOPK=10
echo DEVICE=cpu
) > deeplog_config.txt

python3 ../deeplog/exec_path_anomaly_validate.py
