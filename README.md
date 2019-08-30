# loganalyzer
A log analyzer for DOCSIS system.

Raw log format prerequisite:
Add timestamp like this one "[20190719-08:58:23.748] ". There is a space before log text in each line.

1. Train and test your data:

Put your training & test logs to logs/ and rename them to train.txt and test.txt respectively.
step 1.1:
// to process train data set
1) echo TRAINING=1 > entrance/config.txt
2) run logparser/logpurger.py
3) copy logs/train_new.txt to same folder, rename it to train_new_labeled.txt and label the logs in this file.
4) run logparser/labelprocess.py
5) run logparser/Drain_DOCSIS_demo.py

step 1.2:
// to process test data set
1) echo TRAINING=0 > entrance/config.txt
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

2. Test your data only:

Suppose you already trained your data, you can simply run step 1.2 & 1.3 but no need label the logs/test_new_label.txt. But we still need this file be there.
