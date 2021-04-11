#!/usr/bin/env python3
"""
Description : Parameter anomaly detection
Author      : Wei Han <wei.han@broadcom.com>
License     : MIT
"""
#
# This is not the implementation of DeepLog paper about para value anomaly detection
# We integrate the OSS into DeepLog for the same purpose
#
import os
import sys

curfiledir = os.path.dirname(__file__)
parentdir = os.path.abspath(os.path.join(curfiledir, os.path.pardir))

sys.path.append(parentdir)

import oldschool.cm.knowledgebase as kb

def para_anomaly_det(content, eid, template):
    """ Detect the parameter anomaly by using the OSS

    Arguments
    ---------
    content: the content of the log
    eid: the event id of the log
    template: the template of the log

    Returns
    -------
    True/False: Anomaly is detected (True) or not (False)
    """

    # Convert the log string into token list
    content_ln = content.strip().split()
    template_ln = template.strip().split()

    if len(content_ln) != len(template_ln):
        return False

    # Traverse all <*> tokens in template_ln and save the index
    # Consider cases like '<*>;', '<*>,', etc. Remove the unwanted ';,' in knowledgebase
    idx_list = [idx for idx, value in enumerate(template_ln) if '<*>' in value]
    #print(idx_list)
    param_list = [content_ln[idx] for idx in idx_list]
    #print(param_list)

    # Now we can search in the knowledge base for the current log
    log_fault, _, _ = kb.domain_knowledge(eid, param_list)

    return log_fault
