# Licensed under the MIT License - see LICENSE.txt
""" Domain knowledge base for ftp client Filezilla.
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
            # Responses
            # en.wikipedia.org/wiki/List_of_FTP_server_return_codes
            # ----------------------------------------------------------
            if case('8b23502c'):
                # <TEMPLATE>
                # "Response: <*> Permission denied"
                #
                if int(params[0]) == 550:
                    log_severity = 'error'
                    log_sugg = ("Requested action not taken. File unavailable, "
                                "e.g., file not found, no access.")
                else:
                    log_severity = 'error'
                    log_sugg = "Not defined."
                break

            if case('52dbb961'):
                # <TEMPLATE>
                # "Response: <*> Login <*>"
                #
                if int(params[0]) == 530 and params[1] == 'incorrect.':
                    log_severity = 'error'
                    log_sugg = "Login incorrect."

                break

            # ----------------------------------------------------------
            # Default branch
            # ----------------------------------------------------------
            if case():
                break

        return log_severity, has_context, log_sugg
