@echo off

rem This script updates the template library

(
echo LOG_TYPE=cm
echo TRAINING=1
echo METRICS=0
echo MODEL=TEMPUPDT
echo WINDOW_SIZE=10000
echo WINDOW_STEP=5000
echo TEMPLATE_LIB_SIZE=2000
) > ..\config.txt

rem ---Concatenate multiple raw files into one
rem ---Parameters: script inputLoc filenames outputLoc
set fileList=log_0_3390_labeled.txt/log_2_3390_labeled.txt/log_3_3390_labeled.txt/log_4_3390_labeled.txt/^
normal_0_register_202.txt/normal_1_register_202.txt/normal_2_dbc_202.txt/^
normal_3.txt/temp_updt_0.txt

python ..\..\tools\cat_files.py logs/raw/cm %fileList% logs/cm/train.txt

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Remove labels in logs if any
python ..\..\logparser\extractlabels.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py

rem Separately process temp_updt_1.txt to workaround the Drain initial sim issue
set fileList=temp_updt_1.txt/temp_updt_2.txt/temp_updt_manu.txt/^
temp_updt_bfm_a383.txt/temp_updt_bfm_a350.txt/temp_updt_bfm_a351.txt/temp_updt_bfm_a370.txt/^
temp_updt_bfm_a375.txt/temp_updt_bfm_a416.txt/temp_updt_bfm_a425.txt/temp_updt_bfm_b329.txt/^
temp_updt_bfm_b330.txt/temp_updt_bfm_b331.txt/temp_updt_bfm_b400.txt/temp_updt_bfm_b405.txt/^
temp_updt_bfm_b415.txt/temp_updt_bfm_b451.txt/^
normal_4_register_211.txt/normal_5_otf_mdd_ucd_211.txt/normal_6_dbc_211.txt/normal_7_no_ofdm_211.txt/^
normal_8_no_ofdma_211.txt/normal_9_voice_ipv4_211.txt/normal_10_voice_ipv4_211.txt/^
abnormal_1_diplexer_211.txt/abnormal_2_t4_211.txt/abnormal_3_attnuation_d30_211.txt/^
abnormal_4_diplexer_211.txt/abnormal_5_tod_ipv6_only_211.txt/abnormal_6_tod_ipv6_dual_211.txt/^
abnormal_7_tod_ipv6_apm_211.txt/abnormal_8_scanning_211.txt/^
temp_updt_manu.txt

python ..\..\tools\cat_files.py logs/raw/cm %fileList% logs/cm/train.txt

rem copy ..\..\logs\raw\cm\temp_updt_manu.txt ..\..\logs\cm\train.txt > nul

rem Preprocess
python ..\..\logparser\cm\preprocess.py

rem Remove labels in logs if any
python ..\..\logparser\extractlabels.py

rem Parse the log and update the template library
python ..\..\logparser\cm\parser.py
