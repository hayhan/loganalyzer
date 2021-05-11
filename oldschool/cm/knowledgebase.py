"""
Description : Domain knowledge base for CM / DOCSIS
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""

# Global dict to store the context values
context_store = {'b2079e76': 0}

class SWITCH:
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


def domain_knowledge(template_id, param_list):
    """
    The knowledge base for each meaningful log template

    Arguments
    ---------
    template_id: the Id for each template/event
    param_list: the list of parameters for each log/line

    Returns
    -------
    log_fault: True if a real fault is deteced
    log_description: brief description for the fault
    log_suggestion: suggestion for the possible cause
    """

    # Reset for each log/line
    log_fault = False
    log_description = ""
    log_suggestion = ""

    # Run only once although we use for here. We can use "with SWITCH() as case"
    # But the break can be used in for loop.
    #
    for case in SWITCH(template_id):

        # ---------------------------------------------------------------------
        # Downstream channel status, lock failures
        # ---------------------------------------------------------------------
        if case('bd6df2e3'):
            # TEMPLATE: "DS channel status rxid <*> dcid <*> freq <*> qam <*> fec <*> snr <*> power <*> mod <*>"
            # Check qam and fec status
            if param_list[3] == 'n' or param_list[4] == 'n':
                log_fault = True
                log_description = "QAM/FEC is not locked on DS channle {0}, freq {1}\n" \
                                  .format(param_list[0], param_list[2])
                log_suggestion = "Low power, big noise ...\n"
            # Check DS SNR comparing to threshold. QAM64 18+3=21dB, QAM256 24+3=27dB.
            # Some margins were added.
            if (param_list[7] == 'Qam64' and int(param_list[5]) <= 21) or \
               (param_list[7] == 'Qam256' and int(param_list[5]) <= 27):
                log_fault = True
                log_description += "SNR is low below the threshold and it's not stable\n"
                log_suggestion += "Low power, noise or bad board design all contribute " \
                                  "to low SNR\n"
            # Check the rx power. -15dBmV ~ +15dBmV per spec. Warning if out of this range.
            if int(param_list[6]) > 15 or int(param_list[6]) < -15:
                log_fault = True
                log_description += "DS Power is out of range of -15dBmV ~ +15dBmV per " \
                                   "spec on freq {0}".format(param_list[2])
                log_suggestion += "Adjust the attanuator on DS link. The DS power at 0dBmV " \
                                  "is better."
            break

        if case('c481c3c2'):
            # TEMPLATE: "Telling application we lost lock on QAM channel <*>"
            log_fault = True
            log_description = "Lost lock happens on QAM channel {0}".format(param_list[0])
            log_suggestion = "Disconnected/Bad RF cable, low DS power, etc. Replace cable, " \
                             "decrease DS attanuation ..."
            break

        if case('9f88e081'):
            # TEMPLATE: "BcmCmDsChan:: DsLockFail: hwRxId= <*> dcid= <*> -> enter kDsOperLockToRescueCmts state"
            log_fault = True
            log_description = "DS unlock happens on h/w channel {0}, dcid {1}" \
                              .format(param_list[0], param_list[1])
            log_suggestion = "Downstream is broken ..."
            break

        # ---------------------------------------------------------------------
        # Upstream channel status
        # ---------------------------------------------------------------------
        if case('6e45cf29'):
            # TEMPLATE: "US channel status txid <*> ucid <*> dcid <*> rngsid <*> power <*> freqstart <*> freqend <*> symrate <*> phytype <*> txdata <*>"
            # Check the tx power. Warning if out of 7dBmv ~ 51dBmV.
            # Based on bonding channels and QAMs, 51~61dBmV can be reached but ignore it here.
            if float(param_list[4]) <= 17 or float(param_list[4]) >= 51:
                log_fault = True
                log_description = "US Tx Power is out of range of 17dBmV ~ 51dBmV on " \
                                  "US channel {0} ucid {1} freq {2}\n" \
                                  .format(param_list[0], param_list[1], param_list[5])
                log_suggestion = "Adjust the attanuator on US link. The US Tx power " \
                                 "within 20~50 dBmV is better.\n"
            # Check the data path of tx
            if param_list[9] == 'n':
                log_fault = True
                log_description += "US path has no data, Ranging is NOT ok on " \
                                   "channel {0} ucid {1} freq {2}" \
                                   .format(param_list[0], param_list[1], param_list[5])
                log_suggestion += "Ranging issue, check the ranging process with other " \
                                  "warnings / errors."
            break

        if case('9701dcb3'):
            # TEMPLATE: "BcmCmDocsisCtlThread:: IsUpstreamFreqUsable: cannot use ucid= <*>, chanHiEdgeFreqHz(= <*> ) > maximumDiplexerFrequencyHz= ( <*> )"
            log_fault = True
            log_description = "Some usable US chan ucid {0} freq {1} is beyond the hightest " \
                              "diplexer US range {2}." \
                              .format(param_list[0], param_list[1], param_list[2])
            log_suggestion = "Change the diplexer setting by \"CM/CmHal> diplexer_settings 1\" " \
                             "and disable diplexer auto switch by \"CM/NonVol/CM DOCSIS 3.1 " \
                             "NonVol> enable noDiplexerAutoSwitch 1\". Then write and reboot " \
                             "the board. If issue persists, check the \"CM/NonVol/CM DOCSIS " \
                             "NonVol> diplexer_mask_hw_provision\" and correct the bitmasks " \
                             "according to the schematics."
            break

        # ---------------------------------------------------------------------
        # Ranging, T2/T3/T4 ... timeout
        # ---------------------------------------------------------------------
        if case('85511099'):
            # TEMPLATE: "BcmCmUsRangingState:: T2NoInitMaintEvent: ERROR - no Init Maint map op -> restart error"
            log_fault = True
            log_description = "CM cannot receive broadcast init ranging opportunities"
            log_suggestion = "MAPs are not received on downstream (bad SNR?) " \
                             "or MAP flushing because of CM transmiter problems."
            break

        if case('2fc6ea2f'):
            # TEMPLATE: "BcmCmUsRangingState:: T4NoStationMaintEvent: ERROR - no Station Maint map op error. hwTxId= <*> docs ucid= <*>"
            log_fault = True
            log_description = "T4 timeout happens on Tx channel {0} ucid {1}" \
                              .format(param_list[0], param_list[1])
            log_suggestion = "Usually downstream or upstream has big issues and " \
                             "mac reset might happen."
            break

        if case('33de59d1'):
            # TEMPLATE: "RNG-RSP UsChanId= <*> Stat= <*> "
            # Context TEMPLATE ('b2079e76'): "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
            if param_list[1] == 'Abort':
                log_fault = True
                log_description = "The ranging process is terminated by CMTS on ucid {0}" \
                                  .format(param_list[0])
                # Check the context info, such as the power adjustment of last time
                if context_store['b2079e76'] >= 0:
                    log_suggestion = "Attanuation of upstream is large. Decrease the " \
                                     "upstream attnuation."
                else:
                    log_suggestion = "Attanuation of upstream is small. Increase the " \
                                     "upstream attnuation."
            break

        if case('6ce4761e'):
            # TEMPLATE: "BcmCmUsRangingState:: RngRspMsgEvent: txid= <*> ucid= <*> received RNG-RSP with status= ABORT."
            log_fault = True
            log_description = "The ranging process is terminated by CMTS on " \
                              "hwTxid {0} / ucid {1}".format(param_list[0], param_list[1])
            log_suggestion = "Adjust the US attnuation according to previous suggestion."
            break

        if case('247a95a1'):
            # TEMPLATE: "Logging event: Unicast Ranging Received Abort Response - Re-initializing MAC; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_description = "Ranging is Aborted by CMTS and MAC will be reset"
            log_suggestion = "Attanuation of upstream is too low or high usually. " \
                             "Adjust the US attnuation according to previous suggestion."
            break

        if case('67d9799e'):
            # TEMPLATE: "Logging event: No Ranging Response received - T3 time-out; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_description = "T3 time out happens. CM cannot receive RNG-RSP from CMTS."
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        if case('738aa70f'):
            # TEMPLATE: "Logging event: Started Unicast Maintenance Ranging - No Response received - T3 time-out; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_description = "T3 time out happens for Unicast Maintenance Ranging."
            log_suggestion = "Usually the US attnuation is too high or low, or some " \
                             "kind of CMTS issues ..."
            break

        if case('bd66bf4c') or case('ea78b302') or case('b5dae8ef'):
            # TEMPLATE: "BcmCmUsRangingState:: T3NoRngRspEvent: ERROR - no more RNG-REQ retries."
            # TEMPLATE: "Logging event: <*> consecutive T3 timeouts while trying to range on upstream channel <*>; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            # TEMPLATE: "Logging event: Ranging Request Retries exhausted; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_description = "T3 time out happens. CM cannot receive RNG-RSP from CMTS."
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        if case('4bd32394'):
            # TEMPLATE: "BcmCmUsRangingState:: T3NoRngRspEvent: ERROR - No initial ranging response from CMTS."
            log_fault = True
            log_description = "T3 time out because of no Initial RNG-RSP from CMTS."
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        if case('9006eea9'):
            # TEMPLATE: "BcmCmUsRangingState:: T3NoRngRspEvent: txid= <*> ucid= <*> no RNG-RSP timeout during <*> ranging."
            log_fault = True
            log_description = "T3 time out because of no {%s} RNG-RSP from CMTS." % param_list[2]
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        # ---------------------------------------------------------------------
        # MDD
        # ---------------------------------------------------------------------
        if case('85b2bfec'):
            # TEMPLATE: "BcmCmDsChan:: MddKeepAliveFailTrans: hwRxId= <*> dcid= <*>"
            log_fault = True
            log_description = "MDD cannot be received on h/w channel {0}, dcid {1}" \
                              .format(param_list[0], param_list[1])
            log_suggestion = "Usually downstream is broken, rf cable cut, etc ..."
            break

        if case('877bf6cc'):
            # TEMPLATE: "Logging event: MDD message timeout; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_description = "MDD timeout on CM {0} / CMTS {1}" \
                              .format(param_list[0], param_list[1])
            log_suggestion = "Usually downstream has some problems ..."
            break

        if case('758f2a6a'):
            # TEMPLATE: "BcmCmMacDomainSetsState:: TmNoMddEvent:, MDD timeout during kGatherInitialPriDsMddSets"
            log_fault = True
            log_description = "No MDD received after scaning / locking primary downstream " \
                              "channel."
            log_suggestion = "You need reboot the CMTS if you always see the MDD timeout " \
                             "after scaning / locking EVERY downstream channel."
            break

        # ---------------------------------------------------------------------
        # DHCP, TFTP, TOD, IP, Networks
        # ---------------------------------------------------------------------
        if case('48c6430a'):
            # TEMPLATE: "Logging event: DHCP FAILED - Request sent, No response; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_description = "DHCP provisioning fails on CM WAN Interface"
            log_suggestion = "Check DHCP Server behind CMTS, or DS/US signal quality."
            break

        if case('36cb1e87'):
            # TEMPLATE: "BcmCmDocsisCtlThread:: IpInitErrorEvent: ERROR - IP helper returned DhcpInitFailed error! Restarting!"
            log_fault = True
            log_description = "CM cannot be provisioned to get the IP address from DHCP " \
                              "server on CMTS side"
            log_suggestion = "Usually DHCP server down on CMTS side or upstream signal " \
                             "qulity is not good enough"
            break

        if case('50c4cbad'):
            # TEMPLATE: "Tftp Client:: Send: ERROR - Request Retries > kTftpMaxRequestRetryCount ( <*> ) !"
            log_fault = True
            log_description = "Tftp client on CM cannot connect to the Tftp server behind " \
                              "the CMTS."
            log_suggestion = "Check the Tftp server settings behind the CMTS."
            break

        if case('ce1477b5') or case('de255b44'):
            # TEMPLATE: "Logging event: ToD request sent - No Response received; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            # TEMPLATE: "BcmDocsisTimeOfDayThread:: HandleToD: WARNING - Timed out waiting for a response from the ToD server."
            log_fault = True
            log_description = "ToD request sent - No Response received."
            log_suggestion = "ToD server might not be setup correctly behind the CMTS."
            break

        # ---------------------------------------------------------------------
        # QoS
        # ---------------------------------------------------------------------
        if case('3aad57b2'):
            # TEMPLATE: "Bandwidth request failure! Status = <*>"
            log_fault = True
            log_description = "CM cannot request Upstream bandwidth from CMTS to send data."
            log_suggestion = "Usually upstream signal qulity is not good enough while " \
                             "Ranging is good."
            break

        # ---------------------------------------------------------------------
        # BPI+
        # ---------------------------------------------------------------------
        if case('c44cfdfa'):
            # TEMPLATE: "Logging event: Auth Reject - Unauthorized SAID; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_description = "BPI+ Auth failed."
            log_suggestion = "Check the BPI+ keys on CM, or disable it via CM Config file on CMTS."
            break

        # ---------------------------------------------------------------------
        # Context updates
        # ---------------------------------------------------------------------
        if case('b2079e76'):
            # TEMPLATE: "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
            if param_list[2] == 'Continue':
                context_store.update({'b2079e76': int(param_list[1])})
            break

        # ---------------------------------------------------------------------
        # Default branch
        # ---------------------------------------------------------------------
        if case():
            # Default, no match, could also just omit condition or 'if True'
            break

    return log_fault, log_description, log_suggestion


def aggregate_summaries():
    """
    Aggregate summaries and remove duplicates
    When getting enough user data, we can train a model to find the final summary
    """

    print("Dummy")
