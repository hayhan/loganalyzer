# Licensed under the MIT License - see License.txt
""" This file implements Drain algorithm of log parsing/clustering.
    Reference paper: [Arxiv'18] A Directed Acyclic Graph Approach
    to Online Log Parsing, 2018.
"""
import re
import os
import math
import shutil
import hashlib
from datetime import datetime
import pandas as pd
from tqdm import tqdm


__all__ = ["Para", "Drain"]

# pylint: disable=too-many-instance-attributes:too-few-public-methods
# pylint: disable=too-many-arguments:too-many-public-methods
# pylint: disable=too-many-boolean-expressions:too-many-branches
class Logcluster:
    """ A log cluster/group which maps to a sinale template/event.
        Similarity layer, each cluster/group has its own threshold sim_t
    """
    def __init__(self, log_tmplt='', sim_t=0.1, outcell=None, is_tmplt_new=True, tmplt_id_old=0):
        """
        Attributes
        ----------
        updt_cnt       : the token update count
        is_tmplt_new   : New template that does not exist in library
        tmplt_updt_cnt : the tmplate update count
        tmplt_id_old   : load id from template lib or 0 for a new leaf
        """
        self.log_tmplt = log_tmplt
        self.updt_cnt = 0
        self.sim_t = sim_t
        self.base = -1
        self.initst = -1
        self.outcell = outcell
        self.is_tmplt_new = is_tmplt_new
        self.tmplt_updt_cnt = 0
        self.tmplt_id_old = tmplt_id_old


class Node:
    """ Length layer and Token layer """
    def __init__(self, child_node=None, digit_or_token=None):
        """
        Attributes
        ----------
        child_node     : the child node
        digit_or_token : seq_len - length layer node
                         token_first_key - The first token split
                         token_last_key - The last token split
                         <*> - others-node within each length layer node
        """
        if child_node is None:
            child_node = dict()
        self.child_node = child_node
        self.digit_or_token = digit_or_token


class Ouputcell:
    """ Output layer """
    def __init__(self, log_id_lst=None, parent_lst=None):
        if log_id_lst is None:
            log_id_lst = []
        self.log_id_lst = log_id_lst
        self.out_tmplts = ''
        self.active = True
        if parent_lst is None:
            parent_lst = []
        self.parent_lst = parent_lst


class Para:
    """ Class of parameters """
    def __init__(self, log_format, rex, rex_s_token, raw_file, tmplt_lib,
                 outdir='./', max_child=120, sim_t_m=1, over_wr_lib=False,
                 intmdt=True, aim=True, inc_updt=1, prt_tree=0, nopgbar=0):
        """
        Attributes
        ----------
        log_format  : used to load the needed colomns of raw logs
        raw_file    : the input raw file path/name
        tmplt_lib   : the template library path/name
        save_path   : the output path for structured logs
        rex         : regular expressions used in preprocess in parser
        rex_s_token : pattern list of special tokens that must be same
                      between template and accepted log
        max_child   : max number of children of length layer node
        sim_t_m     : similarity threshold for the merge step
        inc_updt    : incrementally generate the template file.
                      apply to both train and test dataset
        over_wr_lib : overwrite the template lib in persist directory.
                      only apply to train dataset
        prt_tree    : write the tree to a file for debugging
        nopgbar     : disable the progress bar
        intmdt      : save intermediate results to files
        aim         : alway using in-memory data
        """
        self.log_format = log_format
        self.raw_file = raw_file
        self.tmplt_lib = tmplt_lib
        self.save_path = outdir
        self.rex = rex
        self.rex_s_token = rex_s_token
        self.max_child = max_child
        self.sim_t_m = sim_t_m
        self.inc_updt = inc_updt
        self.over_wr_lib = over_wr_lib
        self.prt_tree = prt_tree
        self.nopgbar = nopgbar
        self.intmdt = intmdt
        self.aim = aim


class Drain:
    """ The Drain core """
    def __init__(self, para, raws):
        """
        Attributes
        ----------
        para       : the parameter object from class Para
        raws       : the raw log data, aka. norm data of preprocess
        pointer    : dict of pointers for cache mechanism
        _df_raws   : data frame of raw logs, aka. norm data of preprocess
        _df_tmplts : data frame of templates
        log_id     : log line number in the raw file, debug only
        tree       : the tree, debug only
        """
        self.para = para
        self.raws = raws
        self.pointer = dict()
        self._df_raws = None
        self._df_tmplts = None
        self.log_id = 0
        self.tree = ''


    @staticmethod
    def has_numbers(string):
        """ Check the digits in string """
        # return any(char.isdigit() for char in string)
        # Let us only check the 1st char in string
        return string[0].isdigit()


    @staticmethod
    def has_pun(string): # pylint: disable=unused-argument
        """ Check if there is special character

        pun_str = "#$&'*+,/<=>@^_`|~)"
        pun_chars = set(pun_str)
        return any(char in pun_chars for char in string)
        """
        # We do not check the special char
        return None


    @staticmethod
    def last_token_pun(string):
        """ Check if there is special character """
        pun_str = ".#$&'*+,/<=>@^_`|~)"
        pun_chars = set(pun_str)
        haspuns = any(char in pun_chars for char in string)

        if not haspuns:
            return False
        if re.match(r'^[\w]+[#$&\'*+,/<=>@^_`|~.]+$', string):
            return False
        return True


    @staticmethod
    def delete_all_files(dir_path):
        """ Delete a folder """
        file_list = os.listdir(dir_path)
        for file_name in file_list:
            os.remove(dir_path+file_name)


    def tree_search(self, rtn, seq):
        """
        Browses the tree in order to find a matching cluster to a log
        sequence. It does not generate new node.

        Attributes
        ----------
        rtn    : Root node
        seq    : Log sequence to test
        return : The matching log cluster
        """
        ret_log_cluster = None

        seq_len = len(seq)
        if seq_len in rtn.child_node:
            # Check if there is a key with same length, aka. the cache
            # mechanism. Comment it out because cache mechanism may lead
            # to wrong classification of logs if two or more templates
            # are similar, in other words, the log may be accepted by a
            # template w/ matching similarity which is not the highest.

            # Paper: ret_log_cluster = self.key_tree_search(seq)

            if ret_log_cluster is None:
                # Search the token layer
                token_layer_node = self.token_tree_search(rtn, seq)

                if token_layer_node is not None:
                    # Token layer child node is list, not dict anymore
                    log_cluster_lst = token_layer_node.child_node

                    # Do the fast match under the token layer node
                    ret_log_cluster = self.fast_match(log_cluster_lst, seq)

                    # Update the pointer
                    if ret_log_cluster is not None:
                        self.pointer[len(seq)] = ret_log_cluster
        return ret_log_cluster


    def key_tree_search(self, seq):
        """
        Browses the tree in order to find a matching cluster to a log
        sequence. It does not generate new node.

        Attributes
        ----------
        seq    : Log sequence to test
        return : The matching log cluster
        """
        seq_len = len(seq)

        # If the pointer exist, compare it to the new log first
        log_cluster = self.pointer[seq_len]
        ret_log_cluster = None
        # If first token or last token matches with the key in the tree,
        # then calculate similarity; otherwise, skip.
        if (log_cluster.log_tmplt[0] == seq[0] and not self.has_numbers(seq[0])
                and not self.has_pun(seq[0]))  \
            or (log_cluster.log_tmplt[-1] == seq[-1] and not self.has_numbers(seq[-1])
                and not self.has_pun(seq[-1])) \
            or (log_cluster.log_tmplt[0] == '<*>' and log_cluster.log_tmplt[-1] == '<*>'):

            cur_sim, _= self.seq_dist(log_cluster.log_tmplt, seq)

            if cur_sim >= log_cluster.sim_t:
                ret_log_cluster = log_cluster
        return ret_log_cluster


    def token_tree_search(self, rtn, seq):
        """
        Browse the tree in order to find a matching cluster to a log
        sequence. It does not generate new node.

        Attributes
        ----------
        rtn    : Root node
        seq    : Log sequence to test
        return : The token layer node
        """
        seq_len = len(seq)
        len_layer_nd = rtn.child_node[seq_len]

        # Get the differentiating tokens
        token_first = seq[0]
        token_last = seq[-1]

        token_first_key = '00_Drain_' + token_first
        token_last_key = '-1_Drain_' + token_last

        # Check if the tokens are in the children nodes
        token_layer_node = None
        if token_first_key in len_layer_nd.child_node:
            token_layer_node = len_layer_nd.child_node[token_first_key]

        elif token_last_key in len_layer_nd.child_node and self.has_numbers(token_first):
            token_layer_node = len_layer_nd.child_node[token_last_key]

        elif self.has_numbers(token_first) and self.has_numbers(token_last) \
            and '<*>' in len_layer_nd.child_node:
            token_layer_node = len_layer_nd.child_node['<*>']

        return token_layer_node


    def add_seq_to_tree(self, rtn, log_clust):
        """
        A log sequence cannot be matched by an existing cluster, so add
        the new corresponding log cluster to the tree.

        Attributes
        ----------
        rtn       : Root node
        log_clust : the new Log cluster
        return    : None
        """
        seq_len = len(log_clust.log_tmplt)
        if seq_len not in rtn.child_node:
            # Create a new length layer node and add it to the tree
            len_layer_nd = Node(digit_or_token=seq_len)
            rtn.child_node[seq_len] = len_layer_nd

            # Add others-node for token layer per paper sec 3.4 & Fig. 2
            # Each length layer node has one such node
            new_node = Node(digit_or_token='<*>')
            len_layer_nd.child_node['<*>'] = new_node

        else:
            # If the length layer node already exists, just retrive it
            len_layer_nd = rtn.child_node[seq_len]

        token_first = log_clust.log_tmplt[0]
        token_last = log_clust.log_tmplt[-1]

        token_first_key = '00_Drain_' + token_first
        token_last_key = '-1_Drain_' + token_last

        if token_first_key in len_layer_nd.child_node:
            # The first index token already exists, just retrive it
            token_layer_node = len_layer_nd.child_node[token_first_key]
        elif token_last_key in len_layer_nd.child_node and self.has_numbers(token_first):
            # The last index token already exists, just retrive it
            token_layer_node = len_layer_nd.child_node[token_last_key]
        else:
            # Add the new index node to the token layer
            if len(len_layer_nd.child_node) == self.para.max_child:
                # Length layer node reaches the max, retrive the <*>
                # node instead
                token_layer_node = len_layer_nd.child_node['<*>']
            else:
                # Add new index node starting from here
                if self.has_numbers(token_first):
                    # The first token is a var, then check the last one
                    if self.has_numbers(token_last):
                        # The last token is a var too, then retrive the
                        # <*> token layer node
                        token_layer_node = len_layer_nd.child_node['<*>']
                    else:
                        # Last token is not var, use it as split token
                        new_node = Node(digit_or_token=token_last_key)
                        len_layer_nd.child_node[token_last_key] = new_node
                        token_layer_node = new_node

                else:
                    # The first token is not a var
                    if self.has_numbers(token_last):
                        # The last token is a var
                        new_node = Node(digit_or_token=token_first_key)
                        len_layer_nd.child_node[token_first_key] = new_node
                        token_layer_node = new_node

                    else:
                        # The last token is not a var
                        if self.has_pun(token_last):
                            # The last token has punctuations
                            new_node = Node(digit_or_token=token_first_key)
                            len_layer_nd.child_node[token_first_key] = new_node
                            token_layer_node = new_node

                        elif self.has_pun(token_first):
                            # The first token has puns, the last has not
                            new_node = Node(digit_or_token=token_last_key)
                            len_layer_nd.child_node[token_last_key] = new_node
                            token_layer_node = new_node
                        else:
                            # The first and last token have no puns
                            new_node = Node(digit_or_token=token_first_key)
                            len_layer_nd.child_node[token_first_key] = new_node
                            token_layer_node = new_node

        # Add the new cluster to the leaf node.
        # The child_node here is a list instead of a dictionary anymore
        if len(token_layer_node.child_node) == 0:
            token_layer_node.child_node = [log_clust]
        else:
            token_layer_node.child_node.append(log_clust)


    def seq_dist(self, seq1, seq2):
        """
        Calculate the simlilarity between the template and raw log.
        The seq1 is template

        Attributes
        ----------
        seq1   : the template
        seq2   : the raw log
        return : sim that represents the similarity
                 para_num, the num of parameters
        """

        assert len(seq1) == len(seq2)

        sim_tokens = 0
        para_num = 0
        stop_calc = False
        last_token_same = True
        last_token_para = False
        first_token = True

        for token1, token2 in zip(seq1, seq2):
            # 1).
            # If the first tokens are different between seq1 and seq2,
            # it means the token in the tempalte will be a variable.
            # Drop this case here.
            if first_token:
                first_token = False
                if token1 != token2:
                    stop_calc = True
                    break

            # 2).
            # If the tokens are different between seq1 and seq2 in
            # successive positions, we need give up. It is usually not
            # expected to generate the template like ...<*> <*>...,
            # because they both might not be variables.
            if token1 == '<*>':
                # pylint: disable=no-else-continue
                if last_token_same or last_token_para:
                    para_num += 1
                    # Update last status to current ones. Here we need
                    # consider an exception that if the current token in
                    # raw log (aka token2 in seq2) is <*>, we accept the
                    # ...<*><*>... case in the final template. This is
                    # because the predefined <*> in the raw log always
                    # means correct variables.
                    last_token_same = bool(token2 == '<*>')
                    last_token_para = True
                    # Comment out line below to count <*> in sim_tokens
                    # Paper: continue
                    continue
                else:
                    stop_calc = True
                    break
            if token1 == token2:
                sim_tokens += 1
                # Update last status to current ones
                last_token_same = True
                last_token_para = False
            elif last_token_same:
                # Update last status to current ones
                last_token_same = False
                last_token_para = False
            else:
                # The last tokens and current tokens are all different.
                # Not expected
                stop_calc = True
                break

            # 3).
            # Do not accept seq2 if some special tokens are different
            # between the template seq1 and current log seq2. This can
            # prevent Drain from over-pasering some tokens
            for ptn in self.para.rex_s_token:
                if (ptn.fullmatch(token1) and ptn.fullmatch(token2) and (token1 != token2)) or \
                   (ptn.fullmatch(token1) and ptn.fullmatch(token2) is None) or \
                   (ptn.fullmatch(token2) and ptn.fullmatch(token1) is None):

                    stop_calc = True
                    break

            if stop_calc:
                break

        const_num = len(seq1) - para_num
        if const_num == 0:
            if len(seq1) == 1 and self.has_numbers(seq2[0]):
                sim = 1.0
            else:
                sim = 0.0
        else:
            # See paper formula (1)
            sim = float(sim_tokens) / const_num

        # If 1) the two first tokens between seq1 and seq2, or 2) any
        # two successive tokens between seq1 and seq2, or 3) any special
        # tokens are different, do no match anyway
        if stop_calc:
            sim = 0.0
            para_num = 0

        return sim, para_num


    def fast_match(self, log_clust_lst, seq):
        """
        Find the most suitable log cluster in the leaf node,
        token-wise comparison, used to find the most similar cluster

        Attributes
        ----------
        log_clust_lst : the cluster list
        seq           : the raw log
        return        : the matched log cluster
        """

        ret_log_clust = None

        max_sim = -1
        max_para_num = -1
        max_clust = None

        for log_clust in log_clust_lst:
            cur_sim, cur_para_num = self.seq_dist(log_clust.log_tmplt, seq)
            # When similarity is same, pick the one with more parameters
            if cur_sim>max_sim or (cur_sim==max_sim and cur_para_num>max_para_num):
                max_sim = cur_sim
                max_para_num = cur_para_num
                max_clust = log_clust

        # If similarity is larger than sim_t
        if max_clust is not None and max_sim >= max_clust.sim_t:
            ret_log_clust = max_clust

        return ret_log_clust


    @staticmethod
    def get_template(seq1, seq2):
        """
        Get the new template after comparing the raw log and template.
        The seq1 is raw log and the seq2 is template.

        Attributes
        ----------
        seq1   : the raw log
        seq2   : the template
        return : new_tmplt that represents the new template
                 updt_token_num, num of tokens that are replaced by <*>
        """
        # This func converts the 1st/last token to <*> too. It does not
        # conflict with the <*> token node in paper Fig. 2. The former's
        # still under the "First/Last: xxxx" node per add_seq_to_tree().
        # E.g. If the 1st token is replaced with <*>, it means that the
        # cluster is under a Last split token layer node. We cannot get
        # here in the case that is under a First split token layer node.
        assert len(seq1) == len(seq2)
        new_tmplt = []

        updt_token_num = 0
        for token1, token2 in zip(seq1, seq2):
            if token1 == token2:
                new_tmplt.append(token1)
            else:
                if token2 != '<*>':
                    # The accumulated num of tokens that have been
                    # replaced by <*>. Used to update the similarity
                    # threshold of each cluster.
                    updt_token_num += 1
                new_tmplt.append('<*>')

        return new_tmplt, updt_token_num


    def add_cluster(self, message_lst, id_lst, clust_lst, out_cell_lst, rtn,
                    is_new_tmplt, old_tid):
        """
        Add new cluster to the tree

        Attributes
        ----------
        message_lst  : the log/template token list
        id_lst       : the log line index list
        clust_lst    : the cluster list
        out_cell_lst : the output cell list
        rtn          : the root node
        is_new_tmplt : The template is new or not.
        old_tid      : The old EventId in template lib
        """
        new_out_cell = Ouputcell(log_id_lst=id_lst)

        new_clust = Logcluster(log_tmplt=message_lst, outcell=new_out_cell,
                               is_tmplt_new=is_new_tmplt, tmplt_id_old=old_tid)
        new_out_cell.parent_lst.append(new_clust)

        # Calculate the original num of parameters in the log message
        para_num = 0
        for token in message_lst:
            # In preprocess of Drain domain, we replaced all possible
            # digitals with <*> already. Do not follow the original
            # method in section 4.1.2. in the paper.
            # Paper: if self.has_numbers(token):
            if token == '<*>':
                para_num += 1

        # _ToDo_
        # In case of template loading from library, we should use the
        # saved sim threshold from library instead of paper formula (3)
        # from scratch if the adaptive sim threshold is applied.

        # The sim threshold used by sim layer, see paper formula (3).
        # Paper: new_clust.sim_t = 0.5 * (len(message_lst)-para_num)
        #        / float(len(message_lst))
        # The initial sim_t is lower bound. Inc it to avoid over-parsing
        # new_clust.sim_t = 0.6
        new_clust.sim_t = 0.6 * (len(message_lst)-para_num) / float(len(message_lst))
        new_clust.initst = new_clust.sim_t

        # When the number of para_num is large, the group tends
        # to accept more log messages to generate the template
        new_clust.base = max(2, para_num + 1)

        clust_lst.append(new_clust)
        out_cell_lst.append(new_out_cell)

        self.add_seq_to_tree(rtn, new_clust)

        # Update the cache
        self.pointer[len(message_lst)] = new_clust


    def update_cluster(self, message_lst, log_idx, clust_lst, match_clust):
        """
        Update the cluster in the tree

        Attributes
        ----------
        message_lst : the log/template token list
        log_idx     : the log line id, 1 based
        clust_lst   : the cluster list
        match_clust : the matched cluster after search the tree
        """
        new_tmplt, updt_token_num = self.get_template(message_lst, match_clust.log_tmplt)
        match_clust.outcell.log_id_lst.append(log_idx)

        # Update the cluster
        if ' '.join(new_tmplt) != ' '.join(match_clust.log_tmplt):
            match_clust.log_tmplt = new_tmplt
            match_clust.tmplt_updt_cnt += 1

            # Update the sim threshold of current existing cluster. The
            # sim_t increases with updates, see paper Formula (4) & (5)
            match_clust.updt_cnt = match_clust.updt_cnt + updt_token_num
            match_clust.sim_t = min(1, match_clust.initst + \
                                    0.5*math.log(match_clust.updt_cnt+1, match_clust.base))

            # _Note_
            # For the online update of template, we should save the
            # threshold along with each template in the output_result()
            # if the adaptive theshold is applied.

            # If the merge mechanism is used, then merge the nodes
            # TBD if we need this feature in ML and Oldshchool
            if self.para.sim_t_m < 1:
                self.adjust_output_cell(match_clust, clust_lst)


    def print_tree(self, node, dep):
        """
        Print a tree with depth 'dep', root node is in depth 0
        Print the whole tree with param (root_node, dep=0)
        """
        p_str = ''
        for _ in range(dep):
            p_str += '\t'

        if dep == 0:
            p_str += 'Root Node'
        elif dep == 1:
            p_str += '<' + str(node.digit_or_token) + '>'
        else:
            p_str += node.digit_or_token

        self.tree += (p_str + '\n')

        if dep == 2:
            for child in node.child_node:
                tmp = '\t\t\t' + ' '.join(child.log_tmplt) + '\n'
                self.tree += tmp
            return
        for child in node.child_node:
            self.print_tree(node.child_node[child], dep+1)


    @staticmethod
    def lcs(seq1, seq2):
        """ Return the lcs in a list """
        lengths = [[0 for _ in range(len(seq2)+1)] for _ in range(len(seq1)+1)]
        # The row 0 and column 0 are initialized to 0 already
        for i, _ in enumerate(seq1):
            for j, _ in enumerate(seq2):
                if seq1[i] == seq2[j]:
                    lengths[i+1][j+1] = lengths[i][j] + 1
                else:
                    lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])

        # Read the substring out from the matrix
        result = []
        seq1_len, seq2_len = len(seq1), len(seq2)
        while seq1_len!=0 and seq2_len!=0:
            if lengths[seq1_len][seq2_len] == lengths[seq1_len-1][seq2_len]:
                seq1_len -= 1
            elif lengths[seq1_len][seq2_len] == lengths[seq1_len][seq2_len-1]:
                seq2_len -= 1
            else:
                assert seq1[seq1_len-1] == seq2[seq2_len-1]
                result.insert(0,seq1[seq1_len-1])
                seq1_len -= 1
                seq2_len -= 1
        return result


    def adjust_output_cell(self, log_clust, log_clust_lst):
        """ Adjust the output cell """
        similar_clust = None
        lcs = []
        sim = -1
        log_clust_len = len(log_clust.log_tmplt)

        for cur_log_clust in log_clust_lst:
            cur_clust_len = len(cur_log_clust.log_tmplt)
            if cur_clust_len==log_clust_len or cur_log_clust.outcell==log_clust.outcell:
                continue
            cur_lcs = self.lcs(log_clust.log_tmplt, cur_log_clust.log_tmplt)
            # See paper formula (6)
            cur_sim = float(len(cur_lcs)) / min(log_clust_len, cur_clust_len)

            if cur_sim>sim or (cur_sim==sim and len(cur_lcs)>len(lcs)):
                similar_clust = cur_log_clust
                lcs = cur_lcs
                sim = cur_sim

        if similar_clust is not None and sim>self.para.sim_t_m:
            similar_clust.outcell.log_id_lst = similar_clust.outcell.log_id_lst + \
                                               log_clust.outcell.log_id_lst
            remove_out_cell = log_clust.outcell

            for parent in remove_out_cell.parent_lst:
                similar_clust.outcell.parent_lst.append(parent)
                parent.outcell = similar_clust.outcell

            remove_out_cell.log_id_lst = None
            remove_out_cell.active = False


    def output_result(self, log_clust_lst):
        """ Output the template library and structured logs """
        # No need feature of merging outputcell in Fig. 2 in paper. Just
        # suppose 1-to-1 mapping between template and output always.
        log_templates = [0] * self._df_raws.shape[0]
        log_templateids = [0] * self._df_raws.shape[0]
        log_templateids_old = [0] * self._df_raws.shape[0]
        tmplt_event_lst = []
        for log_clust in log_clust_lst:
            tmplt_str = ' '.join(log_clust.log_tmplt)
            occurrence = len(log_clust.outcell.log_id_lst)
            tmplt_id = hashlib.md5(tmplt_str.encode('utf-8')).hexdigest()[0:8]
            tmplt_id_old = log_clust.tmplt_id_old
            # _ToDo_
            # Should save the sim threshold of tempalte too. It is used
            # to be as the init sim threshold of online template update.

            # Assign template and its id (1 based) to each log.
            for log_id in log_clust.outcell.log_id_lst:
                log_id -= 1
                log_templates[log_id] = tmplt_str
                log_templateids[log_id] = tmplt_id
                log_templateids_old[log_id] = tmplt_id_old

            # Merge the duplicate templates
            # The row[0/1/2/3] maps to items below:
            # [tmplt_id_old, tmplt_id, tmplt_str, occurrence]
            tmplt_unique = True
            for row in tmplt_event_lst:
                if tmplt_id == row[1]:
                    print("Warning: template is duplicated, merging.")
                    tmplt_unique = False
                    if row[0] != row[1]:
                        if tmplt_id == tmplt_id_old:
                            row[0] = row[1]
                    row[3] += occurrence
                    break

            # Drop current template if it is duplicate
            if tmplt_unique:
                tmplt_event_lst.append([tmplt_id_old, tmplt_id, tmplt_str, occurrence])

        # Convert to data frame for saving
        self._df_tmplts = pd.DataFrame(tmplt_event_lst,
            columns=['EventIdOld', 'EventId', 'EventTemplate', 'Occurrences'])

        # Double check if there are any duplicates in templates
        if len(self._df_tmplts['EventId'].values) != len(self._df_tmplts['EventId'].unique()):
            print("Error: template is still duplicated!")

        # Save the template file to data/train or data/test directory
        if self.para.intmdt or not self.para.aim:
            self._df_tmplts.to_csv(os.path.join(self.para.save_path,
                                   os.path.basename(self.para.raw_file) + '_templates.csv'),
                                   columns=['EventId', 'EventTemplate', 'Occurrences'],
                                   index=False)

        # Backup the template library and then update it in data/persist
        # Only do for train data and when template lib inc update enable
        if self.para.over_wr_lib and self.para.inc_updt:
            if os.path.exists(self.para.tmplt_lib):
                shutil.copy(self.para.tmplt_lib, self.para.tmplt_lib+'.old')
            self._df_tmplts.to_csv(self.para.tmplt_lib, index=False,
                                   columns=['EventIdOld', 'EventId', 'EventTemplate'])

        # Save the structured file to data/train or data/test directory
        self._df_raws['EventIdOld'] = log_templateids_old
        self._df_raws['EventId'] = log_templateids
        self._df_raws['EventTemplate'] = log_templates
        # self._df_raws.drop(['Content'], inplace=True, axis=1)
        if self.para.intmdt or not self.para.aim:
            self._df_raws.to_csv(os.path.join(self.para.save_path,
                                 os.path.basename(self.para.raw_file) + '_structured.csv'),
                                 index=False)


    @property
    def df_raws(self):
        """ Get raws in pandas dataframe """
        return self._df_raws


    @property
    def df_tmplts(self):
        """ Get templates in pandas dataframe """
        return self._df_tmplts


    @staticmethod
    def generate_logformat_regex(logformat):
        """ Function to generate regex to split log messages """
        # Suppose the default and standard logformat is:
        #     '<Date> <Time> <Pid> <Level> <Component>: <Content>'
        # Then the output:
        # headers
        #     ['Date', 'Time', 'Pid', 'Level', 'Component', 'Content']
        # regex
        #     (?P<Date>.*?)\s+(?P<Time>.*?)\s+(?P<Pid>.*?)\s+
        #     (?P<Level>.*?)\s+(?P<Component>.*?):\s+(?P<Content>.*?)
        headers = []
        splitters = re.split(r'(<[^<>]+>)', logformat)
        regex = ''
        for k, _ in enumerate(splitters):
            if k % 2 == 0:
                splitter = re.sub(' +', '\\\\s+', splitters[k])
                regex += splitter
            else:
                header = splitters[k].strip('<').strip('>')
                regex += '(?P<%s>.*?)' % header
                headers.append(header)
        # For customized logformat, use it as rex pattern directly.
        # An example of logformat: '(?P<Time>.{m})(?P<Content>.*?)'
        # Note, customeized one should not break headers generation.
        if logformat[0] != '<':
            regex = logformat
        regex = re.compile('^' + regex + '$')
        return headers, regex


    def log_to_dataframe(self, regex, headers):
        """ Function to transform log file to dataframe """
        log_messages = []
        linecount = 0
        # Use in-momory raw data, aka. norm from preprocess by default.
        # Read the norm file if config setting tells us to do so.
        if not self.para.aim:
            with open(self.para.raw_file, 'r', encoding='utf-8') as fin:
                self.raws = fin.readlines()

        for line in self.raws:
            try:
                # Reserve the trailing spaces of each log if it has
                match = regex.search(line.strip('\r\n'))
                message = [match.group(header) for header in headers]
                log_messages.append(message)
                linecount += 1
            except Exception:  # pylint: disable=broad-except
                pass

        logdf = pd.DataFrame(log_messages, columns=headers)
        logdf.insert(0, 'LineId', None)
        logdf['LineId'] = [i + 1 for i in range(linecount)]
        return logdf


    def load_data(self):
        """ Read the raw log data to dataframe """
        headers, regex = self.generate_logformat_regex(self.para.log_format)
        self._df_raws = self.log_to_dataframe(regex, headers)


    def preprocess(self, line):
        """ Pre-process the log in Drain domain """
        for cur_rex in self.para.rex.keys():
            # We put a space before <*>. It does not affect a separate
            # token number. It only affects something like offset:123
            # and the result will be offset: <*>
            line = cur_rex.sub(self.para.rex[cur_rex], line)
        return line


    def load_template_lib(self):
        """ Read the templates from the library to dataframe """
        if self.para.inc_updt and os.path.exists(self.para.tmplt_lib):
            self._df_tmplts = pd.read_csv(self.para.tmplt_lib,
                                          usecols=['EventId', 'EventTemplate'])
        else:
            # Only initialize an empty dataframe
            self._df_tmplts = pd.DataFrame()


    def main_process(self):
        """ The main entry """
        print('Parsing file: ' + self.para.raw_file)
        start_time = datetime.now()

        root_node = Node()

        # List of nodes in the similarity layer containing similar logs
        # clustered by heuristic rules. This list contains all the
        # clusters under root node.
        log_clust_lst = []

        # List of nodes in the final layer that outputs containing logs.
        # Same as log_clust_lst, it contains all the Outputcells under
        # root node too.
        out_cell_lst = []

        # Load the templates from the template library
        self.load_template_lib()

        #
        # Build the tree by using templates from library
        #
        for _, line in self._df_tmplts.iterrows():
            # Split the template into token list
            # Note, reserve the trailing spaces of each log if it has
            log_t = line['EventTemplate'].strip('\r\n')
            token_count = len(log_t.split())
            message_lst = log_t.split(None, token_count-1)

            # Read the old template id for current template
            tid_old = line['EventId']

            # Add new cluster to the tree, and no log id for template
            # The template in each cluster is NOT new
            self.add_cluster(message_lst, [], log_clust_lst, out_cell_lst,
                             root_node, False, tid_old)

        # Load the raw log data
        self.load_data()

        # A lower overhead progress bar
        pbar = tqdm(total=self._df_raws.shape[0], unit='Logs', disable=self.para.nopgbar,
                    bar_format='{l_bar}{bar:40}{r_bar}{bar:-40b}')

        #
        # Process the raw log data
        #
        for _, line in self._df_raws.iterrows():

            log_id = line['LineId']
            # Save the current processing log_id for debugging purpose
            self.log_id = log_id

            # Reserve trailing spaces of each log if it has
            log_t = self.preprocess(line['Content']).strip('\r\n')
            token_count = len(log_t.split())
            message_lst = log_t.split(None, token_count-1)

            # Tree search but not generate node here
            match_clust = self.tree_search(root_node, message_lst)

            if match_clust is None:
                # Match no existing log cluster, so add a new one
                # The template in each cluster is new
                self.add_cluster(message_lst, [log_id], log_clust_lst,
                                 out_cell_lst, root_node, True, 0)
            else:
                # Match an existing cluster, add new log message to it
                self.update_cluster(message_lst, log_id, log_clust_lst, match_clust)

            pbar.update(1)

        pbar.close()
        if not os.path.exists(self.para.save_path):
            os.makedirs(self.para.save_path)

        self.output_result(log_clust_lst)
        print('Parsing done. [Time taken: {!s}]\n'.format(datetime.now() - start_time))

        # Print the tree to a file for debugging...
        if self.para.prt_tree:
            self.print_tree(root_node, 0)
            with open(os.path.join(self.para.save_path, 'tree.txt'), 'w') as drain_tree:
                drain_tree.write(self.tree)
