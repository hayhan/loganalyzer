# Licensed under the MIT License - see LICENSE.txt
""" Domain knowledge base for CM / DOCSIS.
"""
import logging
from typing import List
from analyzer.utils.lang_helper import SWITCH
import analyzer.utils.data_helper as dh
import analyzer.utils.yaml_helper as yh
from analyzer.oldschool import KbBase


__all__ = ["Kb"]

log = logging.getLogger(__name__)


class Kb(KbBase):
    """ The class of domain knowledges """
    def __init__(self):
        # Load the kb in which template's parameters are not cared
        self.kb_nopara: dict = yh.read_yaml(dh.KB_NO_PARA)

        # The context values
        # b2079e76: "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
        self.context_store: dict = {'b2079e76': 0}

        KbBase.__init__(self)

    # pylint: disable=too-many-branches:too-many-statements
    def domain_knowledge(self, template_id: str, param_list: List[str]):
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

        # Check tempaltes who have no parameters being cared
        if template_id in self.kb_nopara:
            log_fault = True
            log_suggestion = self.kb_nopara[template_id]

            return log_fault, log_suggestion

        # Check tempaltes who have parameters being cared
        # Although run only once with 'for' here, we can use 'break'
        for case in SWITCH(template_id):

            # ----------------------------------------------------------
            # Downstream channel status, lock failures
            # ----------------------------------------------------------
            if case('bd6df2e3'):
                # TEMPLATE: "DS channel status rxid <*> dcid <*> freq \
                #            <*> qam <*> fec <*> snr <*> power <*> mod \
                #            <*>"
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

            if case('2f06ae53'):
                # TEMPLATE: "Informing RG CM energy detected = <*>"
                if param_list[0] == '0':
                    log_fault = True
                    log_suggestion = "Cable disconnected, or no any signals on the cable."
                break

            # ----------------------------------------------------------
            # Upstream channel status
            # ----------------------------------------------------------
            if case('6e45cf29'):
                # TEMPLATE: "US channel status txid <*> ucid <*> dcid \
                #            <*> rngsid <*> power <*> freqstart <*> \
                #            freqend <*> symrate <*> phytype <*> \
                #            txdata <*>"
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

            # ----------------------------------------------------------
            # Ranging, ucd, T1/T2/T3/T4 ... timeout, us partial service
            # ----------------------------------------------------------
            if case('33de59d1'):
                # TEMPLATE: "RNG-RSP UsChanId= <*> Stat= <*> "
                # Context TEMPLATE ('b2079e76'): \
                # "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
                if param_list[1] == 'Abort':
                    log_fault = True
                    # Check context, Ex. power adjustment of last time
                    if self.context_store['b2079e76'] >= 0:
                        log_suggestion = "Attanuation of upstream is large. Decrease the " \
                                         "upstream attnuation."
                    else:
                        log_suggestion = "Attanuation of upstream is small. Increase the " \
                                         "upstream attnuation."
                break

            if case('24b26703'):
                # TEMPLATE: "BcmCmUsRangingState:: \
                #            CommonRngErrorHandler: \
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

            # ----------------------------------------------------------
            # DocsisMsgACT
            # ----------------------------------------------------------
            if case('755bd6ed'):
                # TEMPLATE: "BcmCm3dfDocsisMsgACT:: HandleEvent() \
                #            @time= <*> event_code= <*> ( <*> ) "
                if param_list[2] == 'kCmIsUpstreamPartialService':
                    log_fault = True
                    log_suggestion = "Some upstream channels are impaired or filtered."
                break

            # ----------------------------------------------------------
            # Reinit MAC
            # ----------------------------------------------------------
            if case('ec4a6237'):
                # TEMPLATE: "BcmCmDocsisCtlThread:: \
                #            SyncRestartErrorEvent: \
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
                    log_suggestion = "It usually happens when no unicast RNG-RSP on all US " \
                                     "channels. E.g. upstream cable is broken."

                elif param_list[1] == 'RngRspAbortStatus':
                    log_fault = True
                    log_suggestion = "It usually happens when CMTS is not happy with RNG-REQ " \
                                     "although NO T3 timeout on all US channels. E.g. US Tx " \
                                     "power reaches the max or min."

                elif param_list[1] == 'BogusUsTarget':
                    log_fault = True
                    log_suggestion = "It usually happens when no usable UCDs exist."

                elif param_list[1] == 'DsLockFail':
                    log_fault = True
                    log_suggestion = "It usually happens when CM tries to lock DS but RF cut off."

                elif param_list[1] == 'T1NoUcdTimeout':
                    log_fault = True
                    log_suggestion = "It usually happens when no usable UCDs collected on CM."

                break

            # ----------------------------------------------------------
            # Context updates
            # ----------------------------------------------------------
            if case('b2079e76'):
                # TEMPLATE: "RNG-RSP UsChanId= <*> Adj: power= <*> \
                #            Stat= <*> "
                if param_list[2] == 'Continue':
                    self.context_store.update({'b2079e76': int(param_list[1])})
                break

            # ----------------------------------------------------------
            # Default branch
            # ----------------------------------------------------------
            if case():
                # Default, no match, could also just omit condition or
                # 'if True'
                break

        return log_fault, log_suggestion
