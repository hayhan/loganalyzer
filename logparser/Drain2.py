"""
Description : This file implements the Drain algorithm for log parsing
Author      : LogPAI team, modified by Wei Han <wei.han@broadcom.com>
License     : MIT
Paper       : [Arxiv'18] Pinjia He, Jieming Zhu, Hongyu Zhang, Pengcheng Xu,
              Zibin Zheng, and Michael R. Lyu.
              A Directed Acyclic Graph Approach to Online Log Parsing, 2018.
"""

import re
import os
import sys
import numpy as np
import pandas as pd
import gc
import math
import hashlib
from datetime import datetime

curfiledir = os.path.dirname(__file__)
parentdir  = os.path.abspath(os.path.join(curfiledir, os.path.pardir))
sys.path.append(parentdir)

from tools import helper

"""
Note: log group/cluster maps to one single template/event.
"""

# Similarity layer, each cluster/group has its own st
class Logcluster:
    def __init__(self, logTemplate='', st=0.1, outcell=None):
        self.logTemplate = logTemplate
        self.updateCount = 0
        self.st = st
        self.base = -1
        self.initst = -1
        self.outcell = outcell


# Length layer and Token layer
class Node:
    def __init__(self, childD=None, digitOrtoken=None):
        """
        Attributes
        ----------
        childD       : the child node
        digitOrtoken :
                       seqLen - length layer node
                       tokenFirstKey - The first token split
                       tokenLastKey - The last token split
                       <*> - The others-node within each length layer node
        """
        if childD is None:
            childD = dict()
        self.childD = childD
        self.digitOrtoken = digitOrtoken


# Output layer
class Ouputcell:
    def __init__(self, logIDL=None, parentL=None):
        if logIDL is None:
            logIDL = []
        self.logIDL = logIDL
        self.outTemplates = ''
        self.active = True
        if parentL is None:
            parentL = []
        self.parentL = parentL


class Para:
    def __init__(self, log_format, logName, indir='./', outdir='./', \
                 rex={}, rex_s_token=[], maxChild=120, mt=1):
        """
        Attributes
        ----------
        log_format  : used to load the needed colomns of raw logs
        logName     : the name of the input file containing raw log messages
        path        : the input path stores the input log file name
        savePath    : the output path stores the file containing structured logs
        rex         : regular expressions used in preprocessing (step1) [(rex, substitude), ...]
        rex_s_token : the re pattern list for special tokens that must be same between
                      a template and the accepted log
        maxChild    : max number of children of length layer node
        mt          : similarity threshold for the merge step
        """
        self.log_format = log_format
        self.logName = logName
        self.path = indir
        self.savePath = outdir
        self.rex = rex
        self.rex_s_token = rex_s_token
        self.maxChild = maxChild
        self.mt = mt


class Drain:
    def __init__(self, para):
        """
        Attributes
        ----------
        para    : the parameter object from class Para
        pointer : dict of pointers for cache mechanism
        df_log  : data frame of raw logs
        """
        self.para = para
        self.pointer = dict()
        self.df_log = None
        # This logID is used for debugging only
        self.logID = 0


    # Check if there is number
    def hasNumbers(self, s):
        return any(char.isdigit() for char in s)


    # Check if there is special character
    def hasPun(self, s):
        punStr = "#$&'*+,/<=>@^_`|~)"
        punChars = set(punStr)
        return any(char in punChars for char in s)


    # Check if there is special character
    def lastTokenPun(self, s):
        punStr = ".#$&'*+,/<=>@^_`|~)"
        punChars = set(punStr)
        haspuns = any(char in punChars for char in s)

        if not haspuns:
            return False
        if re.match(r'^[\w]+[#$&\'*+,/<=>@^_`|~.]+$', s):
            return False
        return True


    def treeSearch(self, rn, seq):
        """
        Browses the tree in order to find a matching cluster to a log sequence
        It does not generate new node

        Attributes
        ----------
        rn     : Root node
        seq    : Log sequence to test
        return : The matching log cluster
        """

        retLogCluster = None

        seqLen = len(seq)
        if seqLen in rn.childD:
            # Check if there is a key with the same length, namely the cache mechanism
            retLogCluster = self.keyTreeSearch(seq)

            if retLogCluster is None:
                # Search the token layer
                tokenLayerNode = self.tokenTreeSearch(rn, seq)

                if tokenLayerNode is not None:
                    # Note, token layer child note is a list, not dict anymore
                    logClusterList = tokenLayerNode.childD

                    # Do the fast match under the token layer node
                    retLogCluster = self.FastMatch(logClusterList, seq)

                    # Update the pointer
                    if retLogCluster is not None:
                        self.pointer[len(seq)] = retLogCluster
        return retLogCluster


    def keyTreeSearch(self, seq):
        """
        Browses the tree in order to find a matching cluster to a log sequence
        It does not generate new node

        Attributes
        ----------
        seq    : Log sequence to test
        return : The matching log cluster
        """
        seqLen = len(seq)

        # If the pointer exist, compare the pointer and the new log first
        logCluster = self.pointer[seqLen]
        retLogCluster  = None
        # If first token or last token matches with the key in the tree, then calculate similarity; otherwise, skip
        if (logCluster.logTemplate[0] == seq[0] and not self.hasNumbers(seq[0]) and not self.hasPun(seq[0])) \
                or (logCluster.logTemplate[-1] == seq[-1] and not self.hasNumbers(seq[-1]) and not self.hasPun(seq[-1])) \
                or (logCluster.logTemplate[0] == '<*>' and logCluster.logTemplate[-1] == '<*>'):

            curSim, _curNumOfPara = self.SeqDist(logCluster.logTemplate, seq)
            """
            if self.logID == 871:
                print(logCluster.logTemplate)
                print(seq)
                print("cursim %f" % curSim)
            """

            if curSim >= logCluster.st:
                retLogCluster = logCluster
        return retLogCluster


    def tokenTreeSearch(self, rn, seq):
        """
        Browse the tree in order to find a matching cluster to a log sequence
        It does not generate new node

        Attributes
        ----------
        rn     : Root node
        seq    : Log sequence to test
        return : The token layer node
        """
        seqLen = len(seq)
        lenLayerNode = rn.childD[seqLen]

        # Get the differentiating tokens
        tokenFirst = seq[0]
        tokenLast = seq[-1]

        tokenFirstKey = '00_Drain_' + tokenFirst
        tokenLastKey = '-1_Drain_' + tokenLast

        # Check if the tokens are in the children nodes
        tokenLayerNode = None
        if tokenFirstKey in lenLayerNode.childD:
            tokenLayerNode = lenLayerNode.childD[tokenFirstKey]

        elif tokenLastKey in lenLayerNode.childD:
            tokenLayerNode = lenLayerNode.childD[tokenLastKey]

        elif self.hasNumbers(tokenFirst) and self.hasNumbers(tokenLast) and '<*>' in lenLayerNode.childD:
            tokenLayerNode = lenLayerNode.childD['<*>']

        return tokenLayerNode


    def addSeqToTree(self, rn, logClust):
        """
        A log sequence cannot be matched by an existing cluster, so add the
        new corresponding log cluster to the tree

        Attributes
        ----------
        rn       : Root node
        logClust : the new Log cluster
        return   : None
        """
        seqLen = len(logClust.logTemplate)
        if seqLen not in rn.childD:
            # Create a new length layer node and add it to the tree
            lenLayerNode = Node(digitOrtoken=seqLen)
            rn.childD[seqLen] = lenLayerNode

            # Add an others-node for the token layer per paper section 3.4 and Fig. 2
            # Each length layer node has one such node
            newNode = Node(digitOrtoken='<*>')
            lenLayerNode.childD['<*>'] = newNode

        else:
            # If the length layer node already exists, just retrive it
            lenLayerNode = rn.childD[seqLen]

        tokenFirst = logClust.logTemplate[0]
        tokenLast = logClust.logTemplate[-1]

        tokenFirstKey = '00_Drain_' + tokenFirst
        tokenLastKey = '-1_Drain_' + tokenLast

        if (tokenFirstKey) in lenLayerNode.childD:
            # The first index token already exists, just retrive it
            tokenLayerNode = lenLayerNode.childD[tokenFirstKey]
        elif (tokenLastKey) in lenLayerNode.childD:
            # The last index token already exists, just retrive it
            tokenLayerNode = lenLayerNode.childD[tokenLastKey]
        else:
            # Add the new index node to the token layer
            if len(lenLayerNode.childD) == self.para.maxChild:
                # Length layer node reaches the max, retrive the <*> node instead
                tokenLayerNode = lenLayerNode.childD['<*>']
            else:
                # Let us add the new index node starting from here
                #
                if self.hasNumbers(tokenFirst):
                    # The first token is a var, then check the last one
                    #
                    if self.hasNumbers(tokenLast):
                        # The last token is a var too, then retrive the <*> token layer node
                        tokenLayerNode = lenLayerNode.childD['<*>']
                    else:
                        # The last token is not a var, so use it as split token
                        newNode = Node(digitOrtoken=tokenLastKey)
                        lenLayerNode.childD[tokenLastKey] = newNode
                        tokenLayerNode = newNode

                else:
                    # The first token is not a var
                    #
                    if self.hasNumbers(tokenLast):
                        # The last token is a var
                        newNode = Node(digitOrtoken=tokenFirstKey)
                        lenLayerNode.childD[tokenFirstKey] = newNode
                        tokenLayerNode = newNode

                    else:
                        # The last token is not a var
                        #
                        if self.hasPun(tokenLast):
                            # The last token has punctuations
                            newNode = Node(digitOrtoken=tokenFirstKey)
                            lenLayerNode.childD[tokenFirstKey] = newNode
                            tokenLayerNode = newNode

                        elif self.hasPun(tokenFirst):
                            # The first token has punctuations, the last has not
                            newNode = Node(digitOrtoken=tokenLastKey)
                            lenLayerNode.childD[tokenLastKey] = newNode
                            tokenLayerNode = newNode
                        else:
                            # The first and last token have punctuations
                            newNode = Node(digitOrtoken=tokenFirstKey)
                            lenLayerNode.childD[tokenFirstKey] = newNode
                            tokenLayerNode = newNode

        # Add the new cluster to the leaf node.
        # The childD here is a list instead of a dictionary anymore
        if len(tokenLayerNode.childD) == 0:
            tokenLayerNode.childD = [logClust]
        else:
            tokenLayerNode.childD.append(logClust)


    # Calculate the similarity. The seq1 is template
    def SeqDist(self, seq1, seq2):
        """
        Calculate the simlilarity between the template and raw log

        Attributes
        ----------
        seq1   : the template
        seq2   : the raw log
        return : retVal that represents the similarity
                 updateTokenNum, the num of numOfPara (<*>) in current template
        """

        assert len(seq1) == len(seq2)

        simTokens = 0
        numOfPara = 0
        sTokenNoMatch = 0

        for token1, token2 in zip(seq1, seq2):
            if token1 == '<*>':
                numOfPara += 1
                # Comment out line below to count <*> in simTokens
                # Paper: continue
            if token1 == token2:
                simTokens += 1

            # Do not accept seq2 if some special tokens are different
            # between the template seq1 and current log seq2
            # This can prevent Drain from over-pasering some tokens
            for sTokenPattern in self.para.rex_s_token:
                if sTokenPattern.fullmatch(token1) and sTokenPattern.fullmatch(token2) \
                   and (token1 != token2):

                    sTokenNoMatch = 1
                    break

            if sTokenNoMatch:
                break

        numOfConst = len(seq1)-numOfPara
        if numOfConst == 0:
            if len(seq1)==1 and self.hasNumbers(seq2[0]):
                retVal = 1.0
            else:
                retVal = 0.0
        else:
            retVal = float(simTokens) / numOfConst

        # If special tokens are different, no match anyway
        if sTokenNoMatch:
            retVal = 0.0
            numOfPara = 0

        return retVal, numOfPara


    # Find the most suitable log cluster in the leaf node,
    # token-wise comparison, used to find the most similar cluster
    def FastMatch(self, logClustL, seq):
        """
        Find the best matched log cluster in the cluster list
        under certain token layer node

        Attributes
        ----------
        logClustL   : the cluster list
        seq         : the raw log
        return      : the matched log cluster
        """

        retLogClust = None

        maxSim = -1
        maxNumOfPara = -1
        maxClust = None

        for logClust in logClustL:
            curSim, curNumOfPara = self.SeqDist(logClust.logTemplate, seq)
            # When similarity is the same, pick the one with more parameters
            if curSim>maxSim or (curSim==maxSim and curNumOfPara>maxNumOfPara):
                maxSim = curSim
                maxNumOfPara = curNumOfPara
                maxClust = logClust

        # If similarity is larger than st
        if maxClust is not None and maxSim >= maxClust.st:
            retLogClust = maxClust

        return retLogClust


    # The seq1 is raw log and the seq2 is template
    def getTemplate(self, seq1, seq2):
        """
        Get the new template after comparing the raw log and template

        Attributes
        ----------
        seq1   : the raw log
        seq2   : the template
        return : retVal that represents the new template
                 updateTokenNum, the num of tokens that are replaced by <*>
        """
        # This function can convert the 1st/last token to <*> too. It does not
        # conflict with the <*> token node in paper Fig. 2. The former one
        # is still under the "First/Last: xxxx" node per addSeqToTree().
        # E.g. If the 1st token is replaced with <*>, it means the cluster is
        # under a Last split token layer node. We cannot get here in this case
        # under a First split token layer node.
        assert len(seq1) == len(seq2)
        retVal = []

        """
        if self.logID == 788:
            print(seq2)
            print(seq1)
        """

        updatedTokenNum = 0
        for token1, token2 in zip(seq1, seq2):
            if token1 == token2:
                retVal.append(token1)
            else:
                if token2 != '<*>':
                    # The accumulated num of tokens that have been replaced by <*>
                    # used to update the similarity threshold of each cluster 
                    updatedTokenNum += 1
                retVal.append('<*>')

        return retVal, updatedTokenNum


    # Delete a folder
    def deleteAllFiles(self, dirPath):
        fileList = os.listdir(dirPath)
        for fileName in fileList:
            os.remove(dirPath+fileName)


    # Print a tree with depth 'dep', root node is in depth 0
    def printTree(self, node, dep):
        pStr = ''
        for _i in range(dep):
            pStr += '\t'

        if dep == 0:
            pStr += 'Root Node'
        elif dep == 1:
            pStr += '<' + str(node.digitOrtoken) + '>'
        else:
            pStr += node.digitOrtoken

        print (pStr)

        if dep == 2:
            for child in node.childD:
                print ('\t\t\t' + ' '.join(child.logTemplate))
            return 1
        for child in node.childD:
            self.printTree(node.childD[child], dep+1)


    # Return the lcs in a list
    def LCS(self, seq1, seq2):
        lengths = [[0 for j in range(len(seq2)+1)] for i in range(len(seq1)+1)]
        # The row 0 and column 0 are initialized to 0 already
        for i in range(len(seq1)):
            for j in range(len(seq2)):
                if seq1[i] == seq2[j]:
                    lengths[i+1][j+1] = lengths[i][j] + 1
                else:
                    lengths[i+1][j+1] = max(lengths[i+1][j], lengths[i][j+1])

        # Read the substring out from the matrix
        result = []
        lenOfSeq1, lenOfSeq2 = len(seq1), len(seq2)
        while lenOfSeq1!=0 and lenOfSeq2!=0:
            if lengths[lenOfSeq1][lenOfSeq2] == lengths[lenOfSeq1-1][lenOfSeq2]:
                lenOfSeq1 -= 1
            elif lengths[lenOfSeq1][lenOfSeq2] == lengths[lenOfSeq1][lenOfSeq2-1]:
                lenOfSeq2 -= 1
            else:
                assert seq1[lenOfSeq1-1] == seq2[lenOfSeq2-1]
                result.insert(0,seq1[lenOfSeq1-1])
                lenOfSeq1 -= 1
                lenOfSeq2 -= 1
        return result


    def adjustOutputCell(self, logClust, logClustL):

        similarClust = None
        lcs = []
        similarity = -1
        logClustLen = len(logClust.logTemplate)

        for currentLogClust in logClustL:
            currentClustLen = len(currentLogClust.logTemplate)
            if currentClustLen==logClustLen or currentLogClust.outcell==logClust.outcell:
                continue
            currentlcs = self.LCS(logClust.logTemplate, currentLogClust.logTemplate)
            currentSim = float(len(currentlcs)) / min(logClustLen, currentClustLen)

            if currentSim>similarity or (currentSim==similarity and len(currentlcs)>len(lcs)):
                similarClust = currentLogClust
                lcs = currentlcs
                similarity = currentSim

        if similarClust is not None and similarity>self.para.mt:
            similarClust.outcell.logIDL = similarClust.outcell.logIDL + logClust.outcell.logIDL

            removeOutputCell = logClust.outcell

            for parent in removeOutputCell.parentL:
                similarClust.outcell.parentL.append(parent)
                parent.outcell = similarClust.outcell

            removeOutputCell.logIDL = None
            removeOutputCell.active = False


    def outputResult(self, logClustL, rawoutputCellL):

        # Refer to the commented code below in the future if needed
        #
        """
        writeTemplate = open(self.para.savePath + self.para.saveTempFileName, 'w')

        outputCellL = []
        for currenOutputCell in rawoutputCellL:
            if currenOutputCell.active:
                outputCellL.append(currenOutputCell)

        for logClust in logClustL:
            # It is possible that several logClusts point to the same outcell, so
            # we present all possible templates separated by '\t---\t'
            currentTemplate = ' '.join(logClust.logTemplate) + '\t---\t'
            logClust.outcell.outTemplates = logClust.outcell.outTemplates + currentTemplate

        for idx, outputCell in enumerate(outputCellL):
            writeTemplate.write(str(idx+1) + '\t' + outputCell.outTemplates+'\n')

            writeID = open(self.para.savePath + self.para.saveFileName + str(idx+1) + '.txt', 'w')

            for logID in outputCell.logIDL:
                writeID.write(str(logID) + '\n')
            writeID.close()

            # print (outputCell.outTemplates)

        writeTemplate.close()
        """

        # I currently do not need the feature of merging outputcell in Fig. 2 in paper.
        # For simplicity I suppose it is 1-to-1 mapping between template and output
        #
        log_templates = [0] * self.df_log.shape[0]
        log_templateids = [0] * self.df_log.shape[0]
        #df_events = []
        for logClust in logClustL:
            template_str = ' '.join(logClust.logTemplate)
            #occurrence = len(logClust.logIDL)
            template_id = hashlib.md5(template_str.encode('utf-8')).hexdigest()[0:8]
            for logID in logClust.outcell.logIDL:
                logID -= 1
                log_templates[logID] = template_str
                log_templateids[logID] = template_id
            #df_events.append([template_id, template_str, occurrence])

        # A same template might exist in logClustL in several places. Not sure if it is a defect.
        #df_event = pd.DataFrame(df_events, columns=['EventId', 'EventTemplate', 'Occurrences'])
        self.df_log['EventId'] = log_templateids
        self.df_log['EventTemplate'] = log_templates

        # self.df_log.drop(['Content'], inplace=True, axis=1)
        # Save the structured file
        self.df_log.to_csv(os.path.join(self.para.savePath, self.para.logName + '_structured.csv'), index=False)

        occ_dict = dict(self.df_log['EventTemplate'].value_counts())
        df_event = pd.DataFrame()
        df_event['EventTemplate'] = self.df_log['EventTemplate'].unique()
        df_event['EventId'] = df_event['EventTemplate'].map(lambda x: hashlib.md5(x.encode('utf-8')).hexdigest()[0:8])
        df_event['Occurrences'] = df_event['EventTemplate'].map(occ_dict)

        # Save the template file
        df_event.to_csv(os.path.join(self.para.savePath, self.para.logName + '_templates.csv'), \
                        index=False, columns=["EventId", "EventTemplate", "Occurrences"])


    def generate_logformat_regex(self, logformat):
        """ Function to generate regular expression to split log messages
        """
        # Suppose the logformat is:
        #     '<Date> <Time> <Pid> <Level> <Component>: <Content>'
        # Then the output:
        # headers
        #     ['Date', 'Time', 'Pid', 'Level', 'Component', 'Content']
        # regex
        #     (?P<Date>.*?)\s+(?P<Time>.*?)\s+(?P<Pid>.*?)\s+(?P<Level>.*?)\s+(?P<Component>.*?):\s+(?P<Content>.*?)
        headers = []
        splitters = re.split(r'(<[^<>]+>)', logformat)
        regex = ''
        for k in range(len(splitters)):
            if k % 2 == 0:
                splitter = re.sub(' +', '\\\\s+', splitters[k])
                regex += splitter
            else:
                header = splitters[k].strip('<').strip('>')
                regex += '(?P<%s>.*?)' % header
                headers.append(header)
        regex = re.compile('^' + regex + '$')
        return headers, regex


    def log_to_dataframe(self, log_file, regex, headers, logformat):
        """
        Function to transform log file to dataframe
        """
        log_messages = []
        linecount = 0
        with open(log_file, 'r') as fin:
            for line in fin.readlines():
                try:
                    match = regex.search(line.strip())
                    message = [match.group(header) for header in headers]
                    log_messages.append(message)
                    linecount += 1
                except Exception:
                    pass
        logdf = pd.DataFrame(log_messages, columns=headers)
        logdf.insert(0, 'LineId', None)
        logdf['LineId'] = [i + 1 for i in range(linecount)]
        return logdf


    def load_data(self):
        headers, regex = self.generate_logformat_regex(self.para.log_format)
        self.df_log = self.log_to_dataframe(os.path.join(self.para.path, self.para.logName), \
                                            regex, headers, self.para.log_format)


    def preprocess(self, line):
        for currentRex in self.para.rex.keys():
            # I put a space before <*>. It does not affect a sperated token number.
            # It only affects something like offset:123 and the result will be offset: <*>
            line = currentRex.sub(self.para.rex[currentRex], line)
        return line


    def mainProcess(self):
        """
        The main entry
        """
        print('Parsing file: ' + os.path.join(self.para.path, self.para.logName))
        start_time = datetime.now()

        rootNode = Node()

        # List of nodes in the similarity layer containing similar logs clustered by heuristic rules
        # This list contains all the clusters under root node
        logCluL = []

        # List of nodes in the final layer that outputs containing logs
        # Same as logCluL, it contains all the outputCells under root node too
        outputCeL = []

        self.load_data()

        # Init progress bar to 0%
        logsize = self.df_log.shape[0]
        helper.printProgressBar(0, logsize, prefix ='Progress:', suffix='Complete', length=50)

        for rowIndex, line in self.df_log.iterrows():

            logID = line['LineId']
            # Save the current processing logID to class object for debugging
            self.logID = logID

            # LAYER--Preprocessing
            logmessageL = self.preprocess(line['Content']).strip().split()

            # Tree search but not generate node here
            matchCluster = self.treeSearch(rootNode, logmessageL)

            """
            if (logID >= 753 and logID <= 754) or (logID >= 788 and logID <= 789):
                print('line num {}, matchLcuster {}'.format(logID, matchCluster))
            """

            # Match no existing log cluster, so add a new one
            if matchCluster is None:
                newOCell = Ouputcell(logIDL=[logID])
                # newOCell = Ouputcell(logIDL=[line.strip()]) #for debug

                newCluster = Logcluster(logTemplate=logmessageL, outcell=newOCell)
                newOCell.parentL.append(newCluster)

                # The initial value of st is 0.5 times the percentage of non-digit tokens in the log message
                numOfPara = 0
                for token in logmessageL:
                    # In the pre-process of Drain domain, I replaced all possible digital var with <*> already
                    # Do not follow the original method in the paper section 4.1.2
                    # Paper: if self.hasNumbers(token):
                    if token == '<*>':
                        numOfPara += 1

                # The "st" is similarity threshold used by the similarity layer
                # Paper: newCluster.st = 0.5 * (len(logmessageL)-numOfPara) / float(len(logmessageL))
                # The initial st is the lower bound. Make it bigger to avoid over-parsing
                newCluster.st = 0.8
                newCluster.initst = newCluster.st

                # When the number of numOfPara is large, the group tends
                # to accept more log messages to generate the template
                newCluster.base = max(2, numOfPara + 1)

                logCluL.append(newCluster)
                outputCeL.append(newOCell)

                self.addSeqToTree(rootNode, newCluster)

                # Update the cache
                self.pointer[len(logmessageL)] = newCluster

            # Successfully match an existing cluster, add the new log message to the existing cluster
            else:
                newTemplate, numUpdatedToken = self.getTemplate(logmessageL, matchCluster.logTemplate)
                matchCluster.outcell.logIDL.append(logID)
                # matchCluster.outcell.logIDL.append(line.strip()) #for debug

                # Update the cluster
                if ' '.join(newTemplate) != ' '.join(matchCluster.logTemplate):
                    matchCluster.logTemplate = newTemplate

                    # Update the similarity threshold of current existing cluster
                    # The st is increasing with the updates
                    matchCluster.updateCount = matchCluster.updateCount + numUpdatedToken
                    matchCluster.st = min(1, matchCluster.initst + \
                                          0.5*math.log(matchCluster.updateCount+1, matchCluster.base))

                    # If the merge mechanism is used, then merge the nodes
                    # weihan: TBD if I need this feature in ML and Oldshchool
                    if self.para.mt < 1:
                        self.adjustOutputCell(matchCluster, logCluL)

            # Update the progress bar
            helper.printProgressBar(rowIndex+1, logsize, prefix='Progress:', suffix ='Complete', length=50)

        if not os.path.exists(self.para.savePath):
            os.makedirs(self.para.savePath)

        self.outputResult(logCluL, outputCeL)
        print('Parsing done. [Time taken: {!s}]\n'.format(datetime.now() - start_time))

        gc.collect()