# Licensed under the MIT License - see LICENSE.txt
""" Language related helper functions, classes. """

__all__ = [
    "SWITCH",
]


class SWITCH:
    """
    switch/case of python at http://code.activestate.com/recipes/410692/
    Python 3.10 has native switch/case statement. Use the simulated one
    here for back compatible.
    """
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """ Return the match method once, then stop """
        yield self.match

    def match(self, *args):
        """ Indicate whether or not to enter a case suite """
        if self.fall or not args:
            return True
        if self.value in args:
            self.fall = True
            return True
        return False
