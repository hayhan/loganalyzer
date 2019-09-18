#! /bin/bash

python3 ../logparser/logpurger.py
python3 ../logparser/labelprocess.py
python3 ../logparser/Drain_DOCSIS_demo.py

python3 ../detector/demo/DecisionTree_demo.py
#python3 ../detector/demo/LR_demo.py
#python3 ../detector/demo/SVM_demo.py

python3 ../oldschool/analyzer.py