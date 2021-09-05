# Licensed under the MIT License - see LICENSE.txt
""" Domain knowledge base for CM / DOCSIS.
"""
from typing import List
from analyzer.utils.lang_helper import SWITCH


__all__ = ["domain_knowledge"]

# The context values
# b2079e76: "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
context_store = {'b2079e76': 0}


# pylint: disable=too-many-branches:too-many-statements
def domain_knowledge(template_id: str, param_list: List[str]):
    """
    The knowledge base for each meaningful log template

    Arguments
    ---------
    template_id: the Id for each template/event
    param_list: the list of parameters for each log/line

    Returns
    -------
    log_fault: True if a real fault is deteced
    log_suggestion: suggestion for the possible cause
    """

    # Reset for each log/line
    log_fault: bool = False
    log_suggestion: str = ""

    # Although run only once with 'for' here while we can use 'break'
    for case in SWITCH(template_id):

        # --------------------------------------------------------------
        # Downstream channel status, lock failures
        # --------------------------------------------------------------
        if case('bd6df2e3'):
            # TEMPLATE: "DS channel status rxid <*> dcid <*> freq <*> \
            #            qam <*> fec <*> snr <*> power <*> mod <*>"
            # Check qam and fec status
            if param_list[3] == 'n' or param_list[4] == 'n':
                log_fault = True
                log_suggestion = "Low power, big noise. QAM/FEC unlocked.\n"
            # SNR threshold. QAM64 18+3=21dB, QAM256 24+3=27dB.
            if (param_list[7] == 'Qam64' and int(param_list[5]) <= 21) or \
               (param_list[7] == 'Qam256' and int(param_list[5]) <= 27):
                log_fault = True
                log_suggestion += "Low power, noise or bad board design all contribute " \
                                  "to low SNR\n"
            # Check the rx power. -15dBmV ~ +15dBmV per spec.
            if int(param_list[6]) > 15 or int(param_list[6]) < -15:
                log_fault = True
                log_suggestion += "Adjust the attanuator on DS link. The DS power at 0dBmV " \
                                  "is better. It is out of the +/-15dBmV range now."
            break

        if case('c481c3c2'):
            # TEMPLATE: "Telling application we lost lock on QAM \
            #            channel <*>"
            log_fault = True
            log_suggestion = "Disconnected/Bad RF cable, low DS power, etc. Replace cable, " \
                             "decrease DS attanuation ..."
            break

        if case('b90344c4'):
            # TEMPLATE: "Telling application we lost lock on QAM \
            #            primary channel <*>"
            log_fault = True
            log_suggestion = "Disconnected/Bad RF cable, low DS power, etc. Replace cable, " \
                             "decrease DS attanuation ..."
            break

        if case('4df6cac3'):
            # TEMPLATE: "Telling application we lost lock on channel \
            #            <*> ( lostbits= <*> )"
            log_fault = True
            log_suggestion = "Disconnected/Bad RF cable, low DS power, etc. Replace cable, " \
                             "decrease DS attanuation ..."
            break

        if case('9f88e081') or case('8f5e5fd4'):
            # TEMPLATE: "BcmCmDsChan:: DsLockFail: hwRxId= <*> dcid= \
            #            <*> -> enter kDsOperLockToRescueCmts state"
            # TEMPLATE: "BcmCmDsChan:: DsLockFail: rxid= <*> dcid= <*> \
            #            enter recovery state"
            log_fault = True
            log_suggestion = "Downstream is broken and cannot be locked..."
            break

        if case('565f2f45'):
            # TEMPLATE: "1st try PLC NOT locked! Retrying..."
            log_fault = True
            log_suggestion = "RF cable cut, weak downstream OFDM signal, or have noises ..."
            break

        if case('a8db0840'):
            # TEMPLATE: "BcmDocsisCmHalIf:: HandleStatusIndication: \
            #            WARNING - <*> lost PLC Lock"
            log_fault = True
            log_suggestion = "RF cable cut, weak downstream OFDM signal, or have noises ..."
            break

        if case('f228dfa5'):
            # TEMPLATE: "BcmCmDsChanOfdm:: DsLockFail: rxid= <*> dcid= \
            #            <*>"
            log_fault = True
            log_suggestion = "RF cable cut, weak downstream OFDM signal, or have noises ..."
            break

        if case('7f7e47ee'):
            # TEMPLATE: "BcmCmDsOfdmProfileState:: FecLockFail: \
            #            hwRxId= <*> dcid= <*> profId= <*> ( <*> ) \
            #            reason= <*>"
            log_fault = True
            log_suggestion = "RF cable cut, weak downstream OFDM signal, or have noises ..."
            break

        if case('fc738c74') or case('87a34b02'):
            # TEMPLATE: "Cable disconnected"
            # TEMPLATE: "Cable disconnected, Publishing 'cable cut' \
            #            event."
            log_fault = True
            log_suggestion = "Cable disconnected, or no any signals on the cable."
            break

        if case('2f06ae53'):
            # TEMPLATE: "Informing RG CM energy detected = <*>"
            if param_list[0] == '0':
                log_fault = True
                log_suggestion = "Cable disconnected, or no any signals on the cable."
            break

        # --------------------------------------------------------------
        # Recover ds channels
        # --------------------------------------------------------------
        if case('8673876f'):
            # TEMPLATE: "BcmCmDsChan:: RecoverChan: retry -> hwRxId= \
            #            <*> freq= <*> dcid= <*>"
            log_fault = True
            log_suggestion = "DS SC-QAM chan is broken and is trying to recover."
            break

        if case('78a18bef'):
            # TEMPLATE: "BcmCmDsChan:: RecoverChan: rxid= <*> dcid= <*>"
            log_fault = True
            log_suggestion = "DS SC-QAM chan is broken and is trying to recover."
            break

        if case('635494bb'):
            # TEMPLATE: "BcmCmDsChanOfdm:: RecoverChan: rxid= <*> \
            #            dcid= <*>"
            log_fault = True
            log_suggestion = "DS OFDM chan is broken and is trying to recover."
            break

        if case('a379e6bc'):
            # TEMPLATE: "BcmCmDsChanOfdm:: RecoverPlc: rxid= <*> dcid= \
            #            <*> freq= <*>"
            log_fault = True
            log_suggestion = "DS OFDM PLC chan is broken and is trying to recover."
            break

        # --------------------------------------------------------------
        # Upstream channel status
        # --------------------------------------------------------------
        if case('6e45cf29'):
            # TEMPLATE: "US channel status txid <*> ucid <*> dcid <*> \
            #            rngsid <*> power <*> freqstart <*> freqend \
            #            <*> symrate <*> phytype <*> txdata <*>"
            # Check the tx power. Warning if out of 7dBmv ~ 51dBmV.
            # Based on bonding channels and QAMs, 51~61dBmV can be
            # reached but ignore it here.
            if float(param_list[4]) <= 17 or float(param_list[4]) >= 51:
                log_fault = True
                log_suggestion = "Adjust the attanuator on US link. The US Tx power " \
                                 "within 20~50 dBmV is better.\n"
            # Check the data path of tx
            if param_list[9] == 'n':
                log_fault = True
                log_suggestion += "Data path on upstream is not OK."
            break

        if case('9701dcb3'):
            # TEMPLATE: "BcmCmDocsisCtlThread:: IsUpstreamFreqUsable: \
            #            cannot use ucid= <*>, chanHiEdgeFreqHz(= <*> \
            #            ) > \maximumDiplexerFrequencyHz= ( <*> )"
            log_fault = True
            log_suggestion = "Change the diplexer setting by \"CM/CmHal> diplexer_settings 1\" " \
                             "and disable diplexer auto switch by \"CM/NonVol/CM DOCSIS 3.1 " \
                             "NonVol> enable noDiplexerAutoSwitch 1\". Then write and reboot " \
                             "the board. If issue persists, check the \"CM/NonVol/CM DOCSIS " \
                             "NonVol> diplexer_mask_hw_provision\" and correct the bitmasks " \
                             "according to the schematics."
            break

        # --------------------------------------------------------------
        # Ranging, ucd, T1/T2/T3/T4 ... timeout, us partial service
        # --------------------------------------------------------------
        if case('2bdf39df') or case('2b02d4ac') or case('9beb20c5') or case('140fe4f6'):
            # TEMPLATE: "BcmCmMultiUsHelper:: TmUcdRxTimerEvent: ERROR \
            #            -, T1 expired and no usable ucd's received -> \
            #            restart error"
            # TEMPLATE: "BcmCmMultiUsHelper:: TmUcdRxTimerEvent: ERROR \
            #            - UCD rx timer expired and no usable ucd's \
            #            received. -> restart timer."
            # TEMPLATE: "Logging event: No UCDs Received - Timeout; ; \
            #            CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; \
            #            CM-VER= <*>; "
            # TEMPLATE: "Logging event: UCD invalid or channel \
            #            unusable; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= \
            #            <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "No any UCDs or the received UCDs are invalid. E.g. the upstream " \
                             "channel freq > diplexer band edge."
            break

        if case('33de59d1'):
            # TEMPLATE: "RNG-RSP UsChanId= <*> Stat= <*> "
            # Context TEMPLATE ('b2079e76'): \
            # "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
            if param_list[1] == 'Abort':
                log_fault = True
                # Check the context info, such as the power adjustment
                # of last time
                if context_store['b2079e76'] >= 0:
                    log_suggestion = "Attanuation of upstream is large. Decrease the " \
                                     "upstream attnuation."
                else:
                    log_suggestion = "Attanuation of upstream is small. Increase the " \
                                     "upstream attnuation."
            break

        if case('6ce4761e'):
            # TEMPLATE: "BcmCmUsRangingState:: RngRspMsgEvent: txid= \
            #            <*> ucid= <*> received RNG-RSP with status= \
            #            ABORT."
            log_fault = True
            log_suggestion = "Adjust the US attnuation according to previous suggestion."
            break

        if case('247a95a1'):
            # TEMPLATE: "Logging event: Unicast Ranging Received Abort \
            #            Response - Re-initializing MAC; CM-MAC= <*>; \
            #            CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Attanuation of upstream is too low or high usually. " \
                             "Adjust the US attnuation according to previous suggestion."
            break

        if case('85511099'):
            # TEMPLATE: "BcmCmUsRangingState:: T2NoInitMaintEvent: \
            #            ERROR - no Init Maint map op -> restart error"
            log_fault = True
            log_suggestion = "MAPs are not received on downstream (bad SNR?) " \
                             "or MAP flushing because of CM transmiter problems."
            break

        if case('67d9799e'):
            # TEMPLATE: "Logging event: No Ranging Response received - \
            #            T3 time-out; CM-MAC= <*>; CMTS-MAC= <*>; \
            #            CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        if case('738aa70f'):
            # TEMPLATE: "Logging event: Started Unicast Maintenance \
            #            Ranging - No Response received - T3 time-out; \
            #            CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; \
            #            CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Usually the US attnuation is too high or low, or some " \
                             "kind of CMTS issues ..."
            break

        if case('b52f1595'):
            # TEMPLATE: "Logging event: Unicast Maintenance Ranging \
            #            attempted - No response - Retries exhausted; \
            #            CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; \
            #            CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Usually the US attnuation is too high or low, or some " \
                             "kind of CMTS issues ..."
            break

        if case('18157661'):
            # TEMPLATE: "Logging event: B-INIT-RNG Failure - Retries \
            #            exceeded; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= \
            #            <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Usually the US attnuation is too high or low, or some " \
                             "kind of CMTS issues ..."
            break

        if case('bd66bf4c') or case('ea78b302') or case('b5dae8ef'):
            # TEMPLATE: "BcmCmUsRangingState:: T3NoRngRspEvent: ERROR \
            #            - no more RNG-REQ retries."
            # TEMPLATE: "Logging event: <*> consecutive T3 timeouts \
            #            while trying to range on upstream channel \
            #            <*>; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; \
            #            CM-VER= <*>; "
            # TEMPLATE: "Logging event: Ranging Request Retries \
            #            exhausted; CM-MAC= <*>; CMTS-MAC= <*>; \
            #            CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        if case('4bd32394'):
            # TEMPLATE: "BcmCmUsRangingState:: T3NoRngRspEvent: ERROR \
            #            - No initial ranging response from CMTS."
            log_fault = True
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        if case('9006eea9'):
            # TEMPLATE: "BcmCmUsRangingState:: T3NoRngRspEvent: txid= \
            #            <*> ucid= <*> no RNG-RSP timeout during <*> \
            #            ranging."
            log_fault = True
            log_suggestion = "Usually the US attnuation is too high or low, or some kind " \
                             "of CMTS issues ..."
            break

        if case('2fc6ea2f') or case('b73d84d3'):
            # TEMPLATE: "BcmCmUsRangingState:: T4NoStationMaintEvent: \
            #            ERROR - no Station Maint map op error. \
            #            hwTxId= <*> docs ucid= <*>"
            # TEMPLATE: "BcmCmUsRangingState:: T4NoStationMaintEvent: \
            #            ERROR - txid= <*> ucid= <*> no Station Maint \
            #            map op error."
            log_fault = True
            log_suggestion = "Usually downstream or upstream has big issues and " \
                             "mac reset might happen."
            break

        if case('a8b689c1'):
            # TEMPLATE: "Logging event: Received Response to Broadcast \
            #            Maintenance Request, But no Unicast \
            #            Maintenance opportunities received - T4 time \
            #            out; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= <*>; \
            #            CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Usually downstream or upstream has big issues and " \
                             "mac reset might happen."
            break

        if case('24b26703'):
            # TEMPLATE: "BcmCmUsRangingState:: CommonRngErrorHandler: \
            #            txid= <*> ucid= <*> reason= <*> ( <*> )"
            if param_list[3] == 'T4NoStationMaintTimeout':
                log_fault = True
                log_suggestion = "Usually downstream or upstream has big issues and " \
                                 "mac reset might happen."

            elif param_list[3] == 'MaxT3NoRngRspTimeouts':
                log_fault = True
                log_suggestion = "Usually happens when the US channel is broken down. " \
                                 "E.g. US RF cut, noise / distortion on US channel " \
                                 "because of some external spliter / combiner / filter."

            elif param_list[3] == 'RngRspAbortStatus':
                log_fault = True
                log_suggestion = "Usually US attenuation is too high, low or other " \
                                 "reasons that CMTS is not happy with the RNG-REQ."
            break

        if case('e58582d7') or case('6c23502a') or case('55932cf1') or case('d3ae406c'):
            # TEMPLATE: "BcmCmUsSetsState:: UsTimeRefFail: txid= <*> \
            #            ucid= <*> failed to establish upstream time \
            #            sync."
            # TEMPLATE: "BcmCmUsSetsState:: UsTimeRefFail: Failed to \
            #            establish upstream time sync."
            # TEMPLATE: "BcmCmUsSetsState:: UsTimeRefFail: Lost \
            #            upstream time sync."
            # TEMPLATE: "BcmCmUsSetsState:: UsTimeRefFail: txid= <*> \
            #            ucid= <*> lost upstream time sync."
            log_fault = True
            log_suggestion = "Usually upstream is broken, cut off, etc."
            break

        if case('f2b4cdbf'):
            # TEMPLATE: "BcmCmUsRangingState:: RngRspMsgEvent: txid= \
            #            <*> ucid= <*> detected bogus RNG-RSP sid= <*> "
            log_fault = True
            log_suggestion = "Upstream maybe not stable with high attenuation."
            break

        if case('a3d3e790'):
            # TEMPLATE: "Partial Service Upstream Channels:"
            log_fault = True
            log_suggestion = "Some upstream channels are impaired or filtered."
            break

        # --------------------------------------------------------------
        # OFDMA / Tcofdm
        # --------------------------------------------------------------
        if case('cf8606ae'):
            # TEMPLATE: "BcmProcessTcofdmInterrupts:IrqMainStatus:\
            #            ifft_sts_irq:UpstreamPhyChannelNumber= <*>, \
            #            symbol overrun"
            log_fault = True
            log_suggestion = "The upstream pipe is messing up. TCOFDMA block has issues."
            break

        if case('f80f8e58') or case('552d7db9'):
            # TEMPLATE: "Resetting TCOFDM core <*>.."
            # TEMPLATE: "Performing full reset on TCOFDM core <*>.."
            log_fault = True
            log_suggestion = "The upstream pipe is messing up. TCOFDMA block has issues."
            break

        # --------------------------------------------------------------
        # DocsisMsgACT
        # --------------------------------------------------------------
        if case('755bd6ed'):
            # TEMPLATE: "BcmCm3dfDocsisMsgACT:: HandleEvent() @time= \
            #            <*> event_code= <*> ( <*> ) "
            if param_list[2] == 'kCmIsUpstreamPartialService':
                log_fault = True
                log_suggestion = "Some upstream channels are impaired or filtered."
            break

        # --------------------------------------------------------------
        # Reinit MAC
        # --------------------------------------------------------------
        if case('ec4a6237'):
            # TEMPLATE: "BcmCmDocsisCtlThread:: SyncRestartErrorEvent: \
            #            reinit MAC # <*>: <*>"
            if param_list[1] == 'T4NoStationMaintTimeout':
                log_fault = True
                log_suggestion = "Usually downstream or upstream has big issues and " \
                                 "mac reset might happen."

            elif param_list[1] == 'NoMddTimeout':
                log_fault = True
                log_suggestion = "Usually CM scans and locks a non-primary DS channel. " \
                                 "If every DS channel has this MDD timeout, most probably " \
                                 "CMTS has issues. Then try to reboot CMTS."

            elif param_list[1] == 'NegOrBadRegRsp':
                log_fault = True
                log_suggestion = "Some incorrect settings on CM like diplexer might " \
                                 "introduce the wrong values in REG-RSP."

            elif param_list[1] == 'MaxT3NoRngRspTimeouts':
                log_fault = True
                log_suggestion = "This usually happens when no unicast RNG-RSP on all US " \
                                 "channels. E.g. upstream cable is broken."

            elif param_list[1] == 'RngRspAbortStatus':
                log_fault = True
                log_suggestion = "This usually happens when CMTS is not happy with RNG-REQ " \
                                 "although NO T3 timeout on all US channels. E.g. US Tx " \
                                 "power reaches the max or min."

            elif param_list[1] == 'BogusUsTarget':
                log_fault = True
                log_suggestion = "This usually happens when no usable UCDs exist."

            elif param_list[1] == 'DsLockFail':
                log_fault = True
                log_suggestion = "This usually happens when CM tries to lock DS but RF cut off. " \

            elif param_list[1] == 'T1NoUcdTimeout':
                log_fault = True
                log_suggestion = "This usually happens when no usable UCDs collected on CM. " \

            break

        # --------------------------------------------------------------
        # MDD
        # --------------------------------------------------------------
        if case('85b2bfec') or case('8f310cda') or case('c4c2729c') or case('169f89c8'):
            # TEMPLATE: "BcmCmDsChan:: MddKeepAliveFailTrans: hwRxId= \
            #            <*> dcid= <*>"
            # TEMPLATE: "BcmCmDsChan:: MddKeepAliveFailTrans: rxid= \
            #            <*> dcid= <*>"
            # TEMPLATE: "BcmCmDsChanOfdm:: MddKeepAliveFailTrans: \
            #            hwRxId= <*> dcid= <*>"
            # TEMPLATE: "BcmCmDsChanOfdm:: MddKeepAliveFailTrans: \
            #            rxid= <*> dcid= <*>"
            log_fault = True
            log_suggestion = "Usually downstream is broken, rf cable cut, etc ..."
            break

        if case('877bf6cc'):
            # TEMPLATE: "Logging event: MDD message timeout; CM-MAC= \
            #            <*>; CMTS-MAC= <*>; CM-QOS= <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Usually downstream has some problems ..."
            break

        if case('758f2a6a') or case('10ab4b85'):
            # TEMPLATE: "BcmCmMacDomainSetsState:: TmNoMddEvent:, MDD \
            #            timeout during kGatherInitialPriDsMddSets"
            # TEMPLATE: "BcmCmDocsisCtlMsgACT:: HandleEvent() @time= \
            #            <*> event_code= <*> ( <*> ), No MDD timeout \
            #            == > If no MDDs are detected on the \
            #            candidate, Primary Downstream Channel, then \
            #            the CM MUST abort the attempt, to utilize the \
            #            current downstream channel"
            log_fault = True
            log_suggestion = "You need reboot the CMTS if you always see the MDD timeout " \
                             "after scaning / locking EVERY downstream channel."
            break

        # --------------------------------------------------------------
        # DHCP, TFTP, TOD, IP, Networks
        # --------------------------------------------------------------
        if case('48c6430a'):
            # TEMPLATE: "Logging event: DHCP FAILED - Request sent, No \
            #            response; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= \
            #            <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Check DHCP Server behind CMTS, or DS/US signal quality."
            break

        if case('36cb1e87'):
            # TEMPLATE: "BcmCmDocsisCtlThread:: IpInitErrorEvent: \
            #            ERROR - IP helper returned DhcpInitFailed \
            #            error! Restarting!"
            log_fault = True
            log_suggestion = "Usually DHCP server down on CMTS side or upstream signal " \
                             "qulity is not good enough"
            break

        if case('50c4cbad'):
            # TEMPLATE: "Tftp Client:: Send: ERROR - Request Retries > \
            #            kTftpMaxRequestRetryCount ( <*> ) !"
            log_fault = True
            log_suggestion = "Check the Tftp server settings behind the CMTS."
            break

        # --------------------------------------------------------------
        # Registration
        # --------------------------------------------------------------
        if case('5fe4fd5b'):
            # TEMPLATE: "BcmCmDocsisCtlThread:: TxRegAckMsg: ERROR - \
            #            Failed to send the REG-ACK message to the \
            #            CMTS!"
            log_fault = True
            log_suggestion = "Something wrong that REG-ACK cannot or does not send. " \
                             "E.g. Wrong diplexer settings that makes the REG-RSP has " \
                             "some bad values. Then CM refuses to send the ACK."
            break

        if case('3bd0cdca'):
            # TEMPLATE: "BcmDocsisCmHalIf:: TransmitManagementMessage: \
            #            ERROR - MAC Management Message was NOT sent \
            #            after <*> seconds!"
            log_fault = True
            log_suggestion = "Usually some issue happened in upstream MAC module."
            break

        if case('2fee035d'):
            # TEMPLATE: "Logging event: Registration failure, \
            #            re-scanning downstream"
            log_fault = True
            log_suggestion = "Registration failure, re-scanning downstream. Need see other " \
                             "error or warning logs to decide what happened."
            break

        # --------------------------------------------------------------
        # QoS
        # --------------------------------------------------------------
        if case('3aad57b2'):
            # TEMPLATE: "Bandwidth request failure! Status = <*>"
            log_fault = True
            log_suggestion = "Usually upstream signal qulity is not good enough while " \
                             "Ranging is good."
            break

        # --------------------------------------------------------------
        # BPI+
        # --------------------------------------------------------------
        if case('c44cfdfa'):
            # TEMPLATE: "Logging event: Auth Reject - Unauthorized \
            #            SAID; CM-MAC= <*>; CMTS-MAC= <*>; CM-QOS= \
            #            <*>; CM-VER= <*>; "
            log_fault = True
            log_suggestion = "Check the BPI+ keys on CM, or disable it via CM Config file on CMTS."
            break

        # --------------------------------------------------------------
        # Context updates
        # --------------------------------------------------------------
        if case('b2079e76'):
            # TEMPLATE: "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= \
            #            <*> "
            if param_list[2] == 'Continue':
                context_store.update({'b2079e76': int(param_list[1])})
            break

        # --------------------------------------------------------------
        # Default branch
        # --------------------------------------------------------------
        if case():
            # Default, no match, could also just omit condition or
            # 'if True'
            break

    return log_fault, log_suggestion
