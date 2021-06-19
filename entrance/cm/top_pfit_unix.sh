#! /bin/bash

cp ../../logs/raw/cm/labeled/log_0_3390_labeled.txt ../../logs/cm/train.txt
cp ../../logs/raw/cm/labeled/log_2_3390_labeled.txt ../../logs/cm/test.txt
./train_pfit_unix.sh
cp ../../logs/raw/cm/others/log_1_3390_labeled.txt ../../logs/cm/test.txt
./pred_pfit_unix.sh

cp ../../logs/raw/cm/labeled/log_2_3390_labeled.txt ../../logs/cm/train.txt
cp ../../logs/raw/cm/others/log_1_3390_labeled.txt ../../logs/cm/test.txt
./train_pfit_unix.sh
cp ../../logs/raw/cm/labeled/log_3_3390_labeled.txt ../../logs/cm/test.txt
./pred_pfit_unix.sh

cp ../../logs/raw/cm/labeled/log_3_3390_labeled.txt ../../logs/cm/train.txt
cp ../../logs/raw/cm/others/log_1_3390_labeled.txt ../../logs/cm/test.txt
./train_pfit_unix.sh
cp ../../logs/raw/cm/labeled/log_2_3390_labeled.txt ../../logs/cm/test.txt
./pred_pfit_unix.sh

cp ../../logs/raw/cm/labeled/log_4_3390_labeled.txt ../../logs/cm/train.txt
cp ../../logs/raw/cm/labeled/log_3_3390_labeled.txt ../../logs/cm/test.txt
./train_pfit_unix.sh
cp ../../logs/raw/cm/others/log_1_3390_labeled.txt ../../logs/cm/test.txt
./pred_pfit_unix.sh