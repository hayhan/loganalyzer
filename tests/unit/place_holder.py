# Licensed under the MIT License - see LICENSE.txt
""" Unit tests
"""
import pytest


@pytest.mark.great
def test_greater():
    """ Sample code """
    num = 100
    assert num > 100

@pytest.mark.great
def test_greater_equal():
    """ Sample code """
    num = 100
    assert num >= 100

@pytest.mark.others
def test_less():
    """ Sample code """
    num = 100
    assert num < 200
