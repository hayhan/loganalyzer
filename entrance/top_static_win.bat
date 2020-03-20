@echo off
setlocal EnableDelayedExpansion


rem ---Concatenate multiple raw files into one
rem ---parameters: script inputLoc filenames outputLoc
rem ---format: !="!^ is used for spliting a long string
set fileList="log_0_3390_labeled.txt/log_2_3390_labeled.txt/!="!^
log_3_3390_labeled.txt/log_4_3390_labeled.txt"

python ..\tools\cat_files.py logs/raw %fileList% logs/train.txt

copy ..\logs\raw\log_2_3390_labeled.txt ..\logs\test.txt > nul
call .\train_static_win.bat
copy ..\logs\raw\log_1_3390_labeled.txt ..\logs\test.txt > nul
call .\pred_static_win.bat
