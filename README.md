# loganalyzer
A log analyzer for DOCSIS system.

Raw log format prerequisite:
Add timestamp like this one "[20190719-08:58:23.748] ". There is a space before log text in each line.

1. Train and test your data:

Put your training & test logs to logs/ and rename them to train.txt and test.txt respectively.
step 1.1:
// to process train data set
1) make sure TRAINING=1 in entrance/config.txt
2) run logparser/logpurger.py
3) copy logs/train_new.txt to same folder, rename it to train_new_labeled.txt and label the logs in this file.
4) run logparser/labelprocess.py
5) run logparser/Drain_DOCSIS_demo.py

step 1.2:
// to process test data set
1) make sure TRAINING=0 in entrance/config.txt
2) run logparser/logpurger.py
3) copy logs/test_new.txt to same folder, rename it to test_new_labeled.txt and label the logs in this file.
4) run logparser/labelprocess.py
5) run logparser/Drain_DOCSIS_demo.py

step 1.3:
// to train and test your data set
run detector/demo/DecisionTree_demo.py

or
run detector/demo/LR_demo.py

or
run detector/demo/SVM_demo.py

2. Predict your data (no train):

Suppose you already trained your data before, you can simply run command below without training because it will use the training object I saved to the disk.
No need label the logs/test_new_label.txt. But we still need this file be there.

detector/demo/SupervisedLearning_pred.py

For both option 1 and option 2, you can view the result in file anomaly_timestamp.csv under results/test/

--------------------------------------------
There are some scipts can be used to simply the steps above in entrence/. Take care of the labeled files logs/train_new_labeled.txt & test_new_labeled.txt.

--------------------------------------------
The old school way to analyze log based on step 1.1/1.2 above:

(Step 1.3 & Predict use machine learning method. We can also use the old way below.)

oldschool/analyzer.py

Find the result in file analysis_summary.csv under results/test/. Open it with Excel for better view.
