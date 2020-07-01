"""
Description : The DeepLog models for exec path & parameter anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
Paper       : [CCS'17] Min Du, Feifei Li, Guineng Zheng, Vivek Srikumar
              DeepLog: Anomaly Detection and Diagnosis from System Logs
              through Deep Learning, 2017.
"""

import torch
import torch.nn as nn

#########################################################################################
# Execution path model
#########################################################################################

class DeepLogExec(nn.Module):
    """ DeepLog model for exec path anomaly detection
    """
    def __init__(self, device, num_classes, hidden_size=100, num_layers=2, num_dir=1, topk=9):
        """ Initilization
        """
        super(DeepLogExec, self).__init__()
        self.device = device
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_directions = num_dir
        self.topk = topk
        # The cell input dimension is 1 because we use an integer to repsent an event
        self.rnn = nn.LSTM(input_size=1, hidden_size=self.hidden_size,
                           num_layers=self.num_layers, batch_first=True,
                           bidirectional=(self.num_directions == 2))
        self.predict_layer = nn.Linear(self.hidden_size * self.num_directions, num_classes)

    def forward(self, *_input):
        """ Override the forward function
        _input[0] is a 3-Dimension (batch_size x window_size x input_size) tensor: EventSeq
        _output is a 2-Dimension tensor (batch_size x num_classes)
        """
        h_0 = torch.zeros(self.num_layers, _input[0].size(0), self.hidden_size).to(self.device)
        c_0 = torch.zeros(self.num_layers, _input[0].size(0), self.hidden_size).to(self.device)
        _output, _ = self.rnn(_input[0].float(), (h_0, c_0))
        _output = self.predict_layer(_output[:, -1, :])
        return _output
