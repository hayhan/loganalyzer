@echo off

rem ---Concatenate multiple raw files into one
rem ---Parameters: script inputLoc filenames outputLoc
set fileList=log_0_3390_labeled.txt/log_2_3390_labeled.txt/^
log_3_3390_labeled.txt/log_4_3390_labeled.txt

python ..\..\tools\cat_files.py logs/raw/cm %fileList% logs/cm/train.txt 0

copy ..\..\logs\raw\cm\log_2_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\train_static_win.bat
copy ..\..\logs\raw\cm\log_1_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\pred_static_win.bat
