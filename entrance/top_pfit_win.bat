@echo off

copy ..\logs\raw\log_0_3390_labeled.txt ..\logs\train.txt > nul
copy ..\logs\raw\log_2_3390_labeled.txt ..\logs\test.txt > nul
call .\train_pfit_win.bat
copy ..\logs\raw\log_1_3390_labeled.txt ..\logs\test.txt > nul
call .\pred_pfit_win.bat

copy ..\logs\raw\log_2_3390_labeled.txt ..\logs\train.txt > nul
copy ..\logs\raw\log_1_3390_labeled.txt ..\logs\test.txt > nul
call .\train_pfit_win.bat
copy ..\logs\raw\log_3_3390_labeled.txt ..\logs\test.txt > nul
call .\pred_pfit_win.bat

copy ..\logs\raw\log_3_3390_labeled.txt ..\logs\train.txt > nul
copy ..\logs\raw\log_1_3390_labeled.txt ..\logs\test.txt > nul
call .\train_pfit_win.bat
copy ..\logs\raw\log_2_3390_labeled.txt ..\logs\test.txt > nul
call .\pred_pfit_win.bat

copy ..\logs\raw\log_4_3390_labeled.txt ..\logs\train.txt > nul
copy ..\logs\raw\log_3_3390_labeled.txt ..\logs\test.txt > nul
call .\train_pfit_win.bat
copy ..\logs\raw\log_1_3390_labeled.txt ..\logs\test.txt > nul
call .\pred_pfit_win.bat