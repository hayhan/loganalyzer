# Licensed under the MIT License - see LICENSE.txt
""" The base class of knowledge-base.
"""
import logging
from typing import List
from abc import ABC, abstractmethod


__all__ = ["KbBase"]

log = logging.getLogger(__name__)


class KbBase(ABC):
    """ The base class of knowledge-base """
    def __init__(self):
        pass

    @abstractmethod
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

    def place_holder(self):
        """ Place holder to mute warning from PEP 8 """
