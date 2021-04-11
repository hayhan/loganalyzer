#! /bin/bash

# This script does prediction using the DeepLog exec model

# Adapt boardfarm CM logs
#python3 ../../adapter/boardfarm_cm.py

#cp ../../logs/raw/cm/temp_updt_bfm_b433.txt ../../logs/cm/test.txt

# Configure parameters for logparser
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
echo MODEL=DEEPLOG
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ../config.txt

# Preprocess
python3 ../../logparser/cm/preprocess.py

# Parse the log and extract the templates
python3 ../../logparser/cm/parser.py

# Postprocess to recover messed logs
python3 ../../logparser/cm/postprocess.py

# The second time clustering for messed logs
python3 ../../logparser/cm/parser_again.py

# Configure parameters for DeepLog exec model
(
echo LOG_TYPE=cm
echo TRAINING=0
echo METRICS=0
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

#  Do prediction using DeepLog exec model
python3 ../../deeplog/exec_path_anomaly_pred.py
