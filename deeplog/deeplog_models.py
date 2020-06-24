"""
Description : The DeepLog models for exec path & parameter anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
Paper       : [CCS'17] Min Du, Feifei Li, Guineng Zheng, Vivek Srikumar
              DeepLog: Anomaly Detection and Diagnosis from System Logs
              through Deep Learning, 2017.
"""

from collections import defaultdict
import torch
import torch.optim as optim
from torch import nn
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score

#########################################################################################
# Execution path model
#########################################################################################

class DeepLogExec(nn.Module):
    """ DeepLog model for exec path anomaly detection
    """
    def __init__(self, num_classes, hidden_size=100, num_layers=2, num_dir=1, topk=9, device='cpu'):
        """ Initilization
        """
        super(DeepLogExec, self).__init__()
        self.set_device(device)
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_directions = num_dir
        self.topk = topk
        self.rnn = nn.LSTM(input_size=1, hidden_size=self.hidden_size,
                           num_layers=self.num_layers, batch_first=True,
                           bidirectional=(self.num_directions == 2))
        self.criterion = nn.CrossEntropyLoss()
        self.prediction_layer = nn.Linear(self.hidden_size * self.num_directions, num_classes)

    def forward(self, *_input):
        """ Override the forward function
        """
        h_0 = torch.zeros(self.num_layers, _input[0].size(0), self.hidden_size).to(self.device)
        c_0 = torch.zeros(self.num_layers, _input[0].size(0), self.hidden_size).to(self.device)
        _output, _ = self.rnn(_input[0].float(), (h_0, c_0))
        _output = self.fc(_output[:, -1, :])
        return _output

    def set_device(self, dev='cpu'):
        """ Set cpu or gpu for processing data
        """
        if dev != 'cpu' and torch.cuda.is_available():
            self.device = torch.device('cuda')
        else:
            self.device = torch.device('cpu')
