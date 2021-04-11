@echo off

copy ..\..\logs\raw\cm\log_0_3390_labeled.txt ..\..\logs\cm\train.txt > nul
copy ..\..\logs\raw\cm\log_2_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\train_pfit_win.bat
copy ..\..\logs\raw\cm\log_1_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\pred_pfit_win.bat

copy ..\..\logs\raw\cm\log_2_3390_labeled.txt ..\..\logs\cm\train.txt > nul
copy ..\..\logs\raw\cm\log_1_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\train_pfit_win.bat
copy ..\..\logs\raw\cm\log_3_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\pred_pfit_win.bat

copy ..\..\logs\raw\cm\log_3_3390_labeled.txt ..\..\logs\cm\train.txt > nul
copy ..\..\logs\raw\cm\log_1_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\train_pfit_win.bat
copy ..\..\logs\raw\cm\log_2_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\pred_pfit_win.bat

copy ..\..\logs\raw\cm\log_4_3390_labeled.txt ..\..\logs\cm\train.txt > nul
copy ..\..\logs\raw\cm\log_3_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\train_pfit_win.bat
copy ..\..\logs\raw\cm\log_1_3390_labeled.txt ..\..\logs\cm\test.txt > nul
call .\pred_pfit_win.bat