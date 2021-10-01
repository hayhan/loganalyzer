# Licensed under the MIT License - see LICENSE.txt
""" The DeepLog models for exec path & parameter anomaly detection
    Reference paper: [CCS'17] DeepLog: Anomaly Detection and Diagnosis
    from System Logs through Deep Learning, 2017.
"""
import torch
from torch import nn


__all__ = ["DeepLogExec"]


# ----------------------------------------------------------------------
# Execution path model
# ----------------------------------------------------------------------

class DeepLogExec(nn.Module):
    """ DeepLog model for exec path anomaly detection
    """
    # pylint: disable=too-many-arguments
    def __init__(self, device, num_classes, hidden_size=100, num_layers=2, num_dir=1):
        """ Initialization
        """
        super().__init__()
        self.device = device
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.num_directions = num_dir
        # The cell input dimension is 1 because we use an integer to
        # repsent an event. The batch_first is True, then the LSTM input
        # & output first Dimension is batch. The input & output part of
        # (h_n, c_n) are not affected by batch_first.
        self.rnn = nn.LSTM(input_size=1, hidden_size=self.hidden_size,
                           num_layers=self.num_layers, batch_first=True,
                           bidirectional=(self.num_directions == 2))
        self.predict_layer = nn.Linear(self.hidden_size * self.num_directions, num_classes)

    def forward(self, *input_):
        """ Override the forward function

        The input_[0] is a 3-D tensor
        (batch_size x seq_len x input_size): EventSeq.

        The output_ of LSTM is a 3-D tensor
        (batch_size x seq_len x hidden_size).

        The Linear predict layer connects to the last hidden state of
        LSTM, so we only take the last data in dimension 1 ([:, -1, :])
        from LSTM output to predict layer.

        The Linear predict layer input dimension is 2-D tensor
        (batch_size x hidden_size)

        The output_ of predict layer is a 2-D tensor
        (batch_size x num_classes).
        """
        h_0 = torch.zeros(self.num_layers, input_[0].size(0), self.hidden_size).to(self.device)
        c_0 = torch.zeros(self.num_layers, input_[0].size(0), self.hidden_size).to(self.device)
        output_, _ = self.rnn(input_[0].float(), (h_0, c_0))
        output_ = self.predict_layer(output_[:, -1, :])
        return output_
