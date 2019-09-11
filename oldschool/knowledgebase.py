"""
Description : Domain knowledge base
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

#import pandas as pd

class switch(object):
    """
    switch/case of python version at http://code.activestate.com/recipes/410692/
    """
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        """Return the match method once, then stop"""
        yield self.match
        raise StopIteration

    def match(self, *args):
        """Indicate whether or not to enter a case suite"""
        if self.fall or not args:
            return True
        elif self.value in args:
            self.fall = True
            return True
        else:
            return False

def domain_knowledge(templateId, paramList):
    """
    The knowledge base for each meaningful log template

    Arguments
    ---------
    templatedId: the Id for each template/event
    paramList: the list of parameters for each log/line

    Returns
    -------
    logFault: True if a real fault is deteced
    logDescription: brief description for the fault
    logSuggestion: suggestion for the possible cause
    """

    # Reset for each log/line
    logFault = False
    logDescription = ""
    logSuggestion = ""

    for case in switch(templateId):
        if case('c481c3c2'):
            # Template: "Telling application we lost lock on QAM channel <*>"
            logFault = True
            logDescription = "Lost lock happens on QAM channel {0}".format(paramList[0])
            logSuggestion = "disconnected rf cable or low power"
            break

        if case('bd6df2e3'):
            # Template: "DS channel status rxid <*> dcid <*> freq <*> qam <*> fec <*> snr <*> power <*> mod <*>"
            # Check qam and fec status
            if paramList[3] == 'n' or paramList[4] == 'n':
                logFault = True
                logDescription = "QAM/FEC is not locked on DS channle {0}, freq {1}".format(paramList[0], paramList[2])
                logSuggestion = "low power, big noise ..."
            # Check snr
            
            break

        if case('6e45cf29'):
            # Template: "US channel status txid <*> ucid <*> dcid <*> rngsid <*> power <*> freqstart <*> freqend <*> symrate <*> phytype <*> txdata <*>"
            break

        if case(): 
            # Default, no match, could also just omit condition or 'if True'
            #print("something else!")
            break

    return logFault, logDescription, logSuggestion