#! /bin/bash

# This script does prediction using the DeepLog exec model

# Adapt boardfarm CM logs
#python3 ../adapter/boardfarm_cm.py

#cp ../logs/raw/temp_updt_bfm_a350.txt ../logs/test.txt

# Configure parameters for logparser
(
echo TRAINING=0
echo METRICS=0
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > config.txt

# Preprocess
python3 ../logparser/preprocess_cm.py

# Parse the log and extract the templates
python3 ../logparser/drain2_cm.py

# Configure parameters for DeepLog exec model
(
echo TRAINING=0
echo METRICS=0
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

#  Do prediction using DeepLog exec model
python3 ../deeplog/exec_path_anomaly_train.py
