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

    # pylint: disable=too-many-branches,too-many-statements
    def domain_knowledge(self, template_id: str, params: List[str]):
        """
        The knowledge base for each meaningful log template

        Arguments
        ---------
        template_id: the Id for each template/event
        params: the list of parameters for each log/line

        Returns
        -------
        has_context: take into account context of current log or not
        log_severity: fatal/error/warning/info
        log_sugg: suggestion for the possible cause
        """

        # Reset for each log/line
        has_context: bool = True
        log_severity: str = 'info'
        log_sugg: str = ""

        # Check tempaltes who have no parameters being cared
        if template_id in self.kb_nopara:
            log_severity = self.kb_nopara[template_id]['severity']
            has_context = self.kb_nopara[template_id]['contxt']
            log_sugg = self.kb_nopara[template_id]['descpt']

            return log_severity, has_context, log_sugg

        # Check tempaltes who have parameters being cared.
        # Although runs only once with 'for' here, we can use 'break'.
        for case in SWITCH(template_id):

            # ----------------------------------------------------------
            # Downstream channel status, lock failures
            # ----------------------------------------------------------
            if case('bd6df2e3'):
                # <TEMPLATE>
                # "DS channel status rxid <*> dcid <*> freq <*> qam \
                # <*> fec <*> snr <*> power <*> mod <*>"
                #
                # Check qam and fec status
                if params[3] == 'n' or params[4] == 'n':
                    log_severity = 'error'
                    log_sugg = "Low power, big noise. QAM/FEC unlocked. "
                # SNR threshold. QAM64 18+3=21dB, QAM256 24+3=27dB.
                if (params[7] == 'Qam64' and int(params[5]) <= 21) or \
                    (params[7] == 'Qam256' and int(params[5]) <= 27):
                    log_severity = 'error'
                    log_sugg += ("Low power, noise or bad board design all contribute "
                                 "to low SNR. ")
                # Check the rx power. -15dBmV ~ +15dBmV per spec.
                if int(params[6]) > 15 or int(params[6]) < -15:
                    log_severity = 'warning'
                    log_sugg += ("Adjust the attanuator on DS link. The DS power at 0dBmV "
                                 "is better. It is out of the +/-15dBmV range now.")
                break

            if case('2f06ae53'):
                # <TEMPLATE>
                # "Informing RG CM energy detected = <*>"
                #
                if params[0] == '0':
                    log_severity = 'fatal'
                    log_sugg = "Cable disconnected, or no any signals on the cable."
                break

            # ----------------------------------------------------------
            # Upstream channel status
            # ----------------------------------------------------------
            if case('6e45cf29'):
                # <TEMPLATE>
                # "US channel status txid <*> ucid <*> dcid <*> rngsid \
                # <*> power <*> freqstart <*> freqend <*> symrate <*> \
                # phytype <*> txdata <*>"
                #
                # Check the tx power. Warning if out of 7dBmv ~ 51dBmV.
                # Based on bonding channels and QAMs, 51~61dBmV can be
                # reached but ignore it here.
                if float(params[4]) <= 17 or float(params[4]) >= 51:
                    log_severity = 'warning'
                    log_sugg = ("Adjust the attanuator on US link. The US Tx power "
                                "within 20~50 dBmV is better. ")
                # Check the data path of tx
                if params[9] == 'n':
                    log_severity = 'error'
                    log_sugg += "Data path on upstream is not OK."
                break

            # ----------------------------------------------------------
            # Ranging, ucd, T1/T2/T3/T4 ... timeout, us partial service
            # ----------------------------------------------------------
            if case('33de59d1'):
                # <TEMPLATE>
                # "RNG-RSP UsChanId= <*> Stat= <*> "
                #
                # <Context TEMPLATE> ('b2079e76')
                # "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
                #
                if params[1] == 'Abort':
                    log_severity = 'error'
                    # Check context, Ex. power adjustment of last time
                    if self.context_store['b2079e76'] >= 0:
                        log_sugg = ("Attanuation of upstream is large. Decrease the "
                                    "upstream attnuation.")
                    else:
                        log_sugg = ("Attanuation of upstream is small. Increase the "
                                    "upstream attnuation.")
                break

            if case('24b26703') or case('430b6239'):
                # <TEMPLATE> - new
                # "BcmCmUsRangingState:: CommonRngErrorHandler: txid= \
                # <*> ucid= <*> reason= <*> ( <*> )"
                #
                # <TEMPLATE> - old
                # "BcmCmUsRangingState:: CommonRngErrorHandler: \
                # reason= <*> ( <*> ) hwTxId= <*> docs ucid= <*>"
                #
                if template_id == '24b26703':
                    param = params[3]
                else:
                    param = params[1]

                if param == 'T2NoInitMaintTimeout':
                    log_severity = 'error'
                    log_sugg = ("CMTS does not broadcast ranging opportunities in MAPs, "
                                "or this kind of MAPs cannot be received by CM.")

                elif param == 'T4NoStationMaintTimeout':
                    log_severity = 'error'
                    log_sugg = ("Usually downstream or upstream has big issues and "
                                "mac reset might happen.")

                elif param == 'MaxT3NoRngRspTimeouts':
                    log_severity = 'error'
                    log_sugg = ("Usually happens when the US channel is broken down. "
                                "E.g. US RF cut, noise / distortion on US channel "
                                "because of some external spliter / combiner / filter.")

                elif param == 'RngRspAbortStatus':
                    log_severity = 'error'
                    log_sugg = ("Usually US attenuation is too high, low or other "
                                "reasons that CMTS is not happy with the RNG-REQ.")
                break

            if case('51c5ad8f'):
                # <TEMPLATE>
                # "BcmCmUsChanTimerMuxACT:: HandleEvent() @time= <*> \
                # fTimerType= <*> ( <*> ) hwTxId= <*> docs ucid= <*>"
                #
                if params[2] == 'kT2NoInitMaint':
                    log_severity = 'error'
                    log_sugg = ("CMTS does not broadcast ranging opportunities in MAPs, "
                                "or this kind of MAPs cannot be received by CM.")

                elif params[2] == 'kT3NoRngRsp':
                    log_severity = 'warning'
                    log_sugg = ("CMTS does not send back RNG-RSP or the RNG-REQ is not "
                                "sent correctly from CM.")
                break

            # ----------------------------------------------------------
            # DocsisMsgACT
            # ----------------------------------------------------------
            if case('755bd6ed'):
                # <TEMPLATE>
                # "BcmCm3dfDocsisMsgACT:: HandleEvent() @time= <*> \
                # event_code= <*> ( <*> ) "
                #
                if params[2] == 'kCmIsUpstreamPartialService':
                    log_severity = 'warning'
                    log_sugg = "Some upstream channels are impaired or filtered."
                break

            # ----------------------------------------------------------
            # Reinit MAC
            # ----------------------------------------------------------
            if case('ec4a6237'):
                # <TEMPLATE>
                # "BcmCmDocsisCtlThread:: SyncRestartErrorEvent: \
                # reinit MAC # <*>: <*>"
                #
                if params[1] == 'T4NoStationMaintTimeout':
                    log_severity = 'fatal'
                    log_sugg = ("Usually downstream or upstream has big issues and "
                                "mac reset might happen.")

                elif params[1] == 'NoMddTimeout':
                    log_severity = 'warning'
                    log_sugg = ("Usually CM scans and locks a non-primary DS channel. "
                                "If every DS channel has this MDD timeout, most probably "
                                "CMTS has issues. Then try to reboot CMTS.")

                elif params[1] == 'NegOrBadRegRsp':
                    log_severity = 'fatal'
                    log_sugg = ("Some incorrect settings on CM like diplexer might "
                                "introduce the wrong values in REG-RSP.")

                elif params[1] == 'MaxT3NoRngRspTimeouts':
                    log_severity = 'fatal'
                    log_sugg = ("It usually happens when no unicast RNG-RSP on all US "
                                "channels. E.g. upstream cable is broken.")

                elif params[1] == 'RngRspAbortStatus':
                    log_severity = 'fatal'
                    log_sugg = ("It usually happens when CMTS is not happy with RNG-REQ "
                                "although NO T3 timeout on all US channels. E.g. US Tx "
                                "power reaches the max or min.")

                elif params[1] == 'BogusUsTarget':
                    log_severity = 'fatal'
                    log_sugg = "It usually happens when no usable UCDs exist."

                elif params[1] == 'DsLockFail':
                    log_severity = 'fatal'
                    log_sugg = "It usually happens when CM tries to lock DS but RF cut off."

                elif params[1] == 'T1NoUcdTimeout':
                    log_severity = 'fatal'
                    log_sugg = "It usually happens when no usable UCDs collected on CM."

                break

            # ----------------------------------------------------------
            # CM-STATUS / CM-STATUS-ACK
            # ----------------------------------------------------------
            if case('89db902a'):
                # <TEMPLATE>
                # "CM-STATUS-ACK trans= <*> event= <*> ( <*> )"
                #
                if params[2] == 'kCmEvDsOfdmProfNcpLockFail':
                    log_severity = 'error'
                    log_sugg = "Usually downstream channel quality is poor."

                elif params[2] == 'kCmEvDsOfdmProfLockFail':
                    log_severity = 'error'
                    log_sugg = "Usually downstream channel quality is poor."

                elif params[2] == 'kCmEvNonPriDsMddFail':
                    log_severity = 'error'
                    log_sugg = ("CM cannot receive MDD on non-primary DS. Either CMTS "
                                "does not send or CM DS channel quality is poor.")

                break

            # ----------------------------------------------------------
            # Context updates
            # ----------------------------------------------------------
            if case('b2079e76'):
                # <TEMPLATE>
                # "RNG-RSP UsChanId= <*> Adj: power= <*> Stat= <*> "
                #
                if params[2] == 'Continue':
                    self.context_store.update({'b2079e76': int(params[1])})
                break

            # ----------------------------------------------------------
            # Default branch
            # ----------------------------------------------------------
            if case():
                break

        return log_severity, has_context, log_sugg
