@echo off

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=1
echo MODEL=DT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem ---Concatenate multiple raw files into one
rem ---Parameters: script inputLoc filenames
rem Note: Detector needs monotonic increasing timestamp, so manually list files
rem and cat them in sequence.
set fileList=log_0_3390_labeled.txt/log_2_3390_labeled.txt/^
log_3_3390_labeled.txt/log_4_3390_labeled.txt

python ..\..\logparser\cat_files.py logs/raw/cm/labeled %fileList%

copy ..\..\logs\raw\cm\labeled\log_2_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\train_static_win.bat
copy ..\..\logs\raw\cm\others\log_1_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\pred_static_win.bat
