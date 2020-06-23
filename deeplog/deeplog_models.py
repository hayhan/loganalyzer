"""
Description : The DeepLog models for exec path & parameter anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
Paper       : [CCS'17] Min Du, Feifei Li, Guineng Zheng, Vivek Srikumar
              DeepLog: Anomaly Detection and Diagnosis from System Logs
              through Deep Learning, 2017.
"""


#########################################################################################
# Execution path model
#########################################################################################

use dataset and dataloader with datadict
do not use class function for train/evaluate

ToDo:
1. Verify batch size result with Dataset and TensorDataset
2. 