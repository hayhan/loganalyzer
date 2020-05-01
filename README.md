# **Log Analyzer**

## **Usage**

### Raw log format prerequisite
Add timestamp like this one "[20190719-08:58:23.748] " at the start of each line.

### Label your training logs
Put a string "abn: " after the timestamp for the anomaly log. If it is a multi-line log, just label the first line.

### Train / Validate the model
1) copy the labeled training logs file to logs/train.txt. Copy the labeled validating logs file to logs/test.txt.
2) run entrance/train_unix.sh or train_win.bat.
3) above scripts have some parameters that you can change, e.g. select different model, window size, etc.

### Predict
1) copy the raw logs file to logs/test.txt.
2) run entrance/pred_unix.sh or pred_win.bat.
3) anomalies are save to results/test/anomaly_timestamp.csv.

### The Old School System
The step 3) of Predict also runs the OSS to get another analyzing result, which is save to results/test/analysis_summary.csv.

## **Porting to Other Systems**

By default, the logs come from Cable Modem system. To analyze other system's logs, need port several application dependent files as following:
logparser/preporcess_cm.py
logparser/Drain2_cm.py
oldschool/knowledgebase_cm.py
