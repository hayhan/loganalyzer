# Licensed under the MIT License - see LICENSE.txt
""" Unit tests
"""
import math
import pytest


@pytest.mark.square
def test_sqrt():
    """ Sample code """
    num = 25
    assert math.sqrt(num) == 5

@pytest.mark.square
def testsquare():
    """ Sample code """
    num = 7
    assert num*num == 40

@pytest.mark.others
def test_equality():
    """ Sample code """
    assert 10 == 11
