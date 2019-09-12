"""
Description : Domain knowledge base
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

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

    # Run only once although we use for here. We can use "with switch() as case"
    # But the break can be used in for loop.
    #
    for case in switch(templateId):
        if case('c481c3c2'):
            # TEMPLATE: "Telling application we lost lock on QAM channel <*>"
            logFault = True
            logDescription = "Lost lock happens on QAM channel {0}".format(paramList[0])
            logSuggestion = "disconnected rf cable or low power"
            break

        if case('bd6df2e3'):
            # TEMPLATE: "DS channel status rxid <*> dcid <*> freq <*> qam <*> fec <*> snr <*> power <*> mod <*>"
            # Check qam and fec status
            if paramList[3] == 'n' or paramList[4] == 'n':
                logFault = True
                logDescription = "QAM/FEC is not locked on DS channle {0}, freq {1}".format(paramList[0], paramList[2])
                logSuggestion = "low power, big noise ...\n"
            # Check DS SNR comparing to threshold. QAM64 18+3=21dB, QAM256 24+3=27dB. Some margins were added.
            if (paramList[7] == 'Qam64' and int(paramList[5]) <= 21) or (paramList[7] == 'Qam256' and int(paramList[5]) <= 27):
                logFault = True
                logDescription += "\nSNR is low below the threshold and it's not stable"
                logSuggestion += "\nlow power, noise or bad board design all contribute to low SNR"
            # Check the rx power. -15dBmV ~ +15dBmV per spec. Warning if out of this range.
            if int(paramList[6]) > 15 or int(paramList[6]) < -15:
                logFault = True
                logDescription += "\nDS Power is out of range of -15dBmV ~ +15dBmV per spec on freq {0}".format(paramList[2])
                logSuggestion += "\nAdjust the attanuator on DS link. The DS power at 0dBmV is better."
            break

        if case('6e45cf29'):
            # TEMPLATE: "US channel status txid <*> ucid <*> dcid <*> rngsid <*> power <*> freqstart <*> freqend <*> symrate <*> phytype <*> txdata <*>"
            # Check the tx power. Warning if out of 7dBmv ~ 51dBmV. Based on bonding channels and QAMs, 51~61dBmV can be reached but ignore it here.
            if int(paramList[4]) <= 17 or int(paramList[4]) >= 51:
                logFault = True
                logDescription = "US Tx Power is out of range of 17dBmV ~ 51dBmV on US channel {0} ucid {1} freq {2}" \
                                 .format(paramList[0], paramList[1], paramList[5])
                logSuggestion = "Adjust the attanuator on US link. The US Tx power within 20~50 dBmV is better."
            # Check the data path of tx
            if paramList[9] == 'n':
                logFault = True
                logDescription += "\nUS path has no data, Ranging is NOT ok on channel {0} ucid {1} freq {2}" \
                                  .format(paramList[0], paramList[1], paramList[5])
                logSuggestion += "\nRanging issue, check the ranging process"
            break

        if case('7511ac2a'):
            # TEMPLATE: "RNG-RSP UsChanId= <*> Stat= <*>"
            if paramList[1] == 'Abort':
                logFault = True
                logDescription = "The ranging process is terminated by CMTS on ucid {0}".format(paramList[0])
                logSuggestion = "Attanuation of upstream is too low or high usually."
            break

        if case('2fc6ea2f'):
            # TEMPLATE: "BcmCmUsRangingState:: T4NoStationMaintEvent: ERROR - no Station Maint map op error. hwTxId= <*> docs ucid= <*>"
            logFault = True
            logDescription = "T4 timeout happens on Tx channel {0} ucid {1}".format(paramList[0], paramList[1])
            logSuggestion = "Usually downstream or upstream has big issues and mac reset might happen"
            break

        if case('fdc567db'):
            # TEMPLATE: "BcmCmDocsisCtlThread:: IsUpstreamFreqUsable: ( CmDocsisCtlThread ) cannot use ucid= <*>, chanHiEdgeFreqHz(= <*> ) > maximumDiplexerFrequencyHz= ( <*> )"
            logFault = True
            logDescription = "Some usable US chan ucid {0} freq {1} is beyond the hightest diplexer US range {2}." \
                             .format(paramList[0], paramList[1], paramList[2])
            logSuggestion = "Change the diplexer settings by CM/CmHal> diplexer_settings 0/1 and " \
                            "CM/NonVol/CM DOCSIS NonVol> diplexer_mask_hw_provision or you might " \
                            "need check the diplexer h/w to see if it supports"
            break

        if case(): 
            # Default, no match, could also just omit condition or 'if True'
            break

    return logFault, logDescription, logSuggestion