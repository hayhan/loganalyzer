#! /bin/bash

cp ../logs/raw/log_0_3390_labeled.txt ../logs/train.txt
cp ../logs/raw/log_2_3390_labeled.txt ../logs/test.txt
./train_pfit_unix.sh
cp ../logs/raw/log_1_3390_labeled.txt ../logs/test.txt
./pred_pfit_unix.sh

cp ../logs/raw/log_2_3390_labeled.txt ../logs/train.txt
cp ../logs/raw/log_1_3390_labeled.txt ../logs/test.txt
./train_pfit_unix.sh
cp ../logs/raw/log_3_3390_labeled.txt ../logs/test.txt
./pred_pfit_unix.sh

cp ../logs/raw/log_3_3390_labeled.txt ../logs/train.txt
cp ../logs/raw/log_1_3390_labeled.txt ../logs/test.txt
./train_pfit_unix.sh
cp ../logs/raw/log_3_3390_labeled.txt ../logs/test.txt
./pred_pfit_unix.sh
