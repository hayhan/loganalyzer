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
import time
import numpy as np
import gc
import math

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
            childD: The child node
            digitOrtoken:
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
    def __init__(self, rex=None, path='', maxChild=120, logName='rawlog.log', \
                 removeCol=None, savePath='./results/', saveFileName='template', \
                 saveTempFileName='logTemplates.txt', delimiters=' ', mt=1):
        """
        Attributes
        ----------
            rex: regular expressions used in preprocessing (step1) [(rex, substitude), ...]
            path: the input path stores the input log file name
            maxChild: max number of children of length layer node
            logName: the name of the input file containing raw log messages
            removeCol: the index of column needed to remove
            savePath: the output path stores the file containing structured logs
            saveTempFileName: the output template file name
            mt: similarity threshold for the merge step
        """
        self.path = path
        self.maxChild = maxChild
        self.logName = logName
        self.savePath = savePath
        self.saveFileName = saveFileName
        self.saveTempFileName = saveTempFileName
        self.delimiters = delimiters
        self.mt = mt

        if removeCol is None:
            removeCol = []
        self.removeCol = removeCol

        if rex is None:
            rex = []
        self.rex = rex


class Drain:
    def __init__(self, para):
        self.para = para
        # create the list of the pointer
        self.pointer = dict()

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
            rn: Root node
            seq: Log sequence to test
            return: The matching log cluster
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
            seq: Log sequence to test
            return: The matching log cluster
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

            if curSim >= logCluster.st:
                retLogCluster = logCluster
        return retLogCluster

    def tokenTreeSearch(self, rn, seq):
        """
        Browse the tree in order to find a matching cluster to a log sequence
        It does not generate new node

        Attributes
        ----------
            rn: Root node
            seq: Log sequence to test
            return: The token layer node
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
            rn: Root node
            logClust: the new Log cluster
            return: None
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
            # weihan: TBD if this algorithm reasonable
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
        assert len(seq1) == len(seq2)

        simTokens = 0
        numOfPara = 0

        for token1, token2 in zip(seq1, seq2):
            if token1 == '<*>':
                numOfPara += 1
                continue
            if token1 == token2:
                simTokens += 1

        numOfConst = len(seq1)-numOfPara
        if numOfConst == 0:
            if len(seq1)==1 and self.hasNumbers(seq2[0]):
                retVal = 1.0
            else:
                retVal = 0.0
        else:
            retVal = float(simTokens) / numOfConst

        return retVal, numOfPara


    # Find the most suitable log cluster in the leaf node,
    # token-wise comparison, used to find the most similar cluster
    def FastMatch(self, logClustL, seq):
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
        assert len(seq1) == len(seq2)
        retVal = []

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


    def mainProcess(self):

        t1 = time.time()
        rootNode = Node()

        # List of nodes in the similarity layer containing similar logs clustered by heuristic rules
        # This list contains all the clusters under root node
        logCluL = []

        # List of nodes in the final layer that outputs containing logs
        # Same as logCluL, it contains all the outputCells under root node too
        outputCeL = []

        with open(self.para.path+self.para.logName) as lines:
            for line in lines:
                logID = int(line.split('\t')[0])
                # logmessageL = re.split(self.para.delimiters, line.strip().split('\t')[1])
                logmessageL = line.strip().split('\t')[1].split()

                if self.para.removeCol is not None:
                    logmessageL = [word for i, word in enumerate(logmessageL) if i not in self.para.removeCol]
                cookedLine = ' '.join(logmessageL)


                # LAYER--Preprocessing
                for currentRex in self.para.rex:
                    cookedLine = re.sub(currentRex[0], currentRex[1], cookedLine)

                logmessageL = cookedLine.split()

                # Length zero logs, which are anomaly cases
                if len(logmessageL) == 0:
                    continue

                # Tree search but not generate node here
                matchCluster = self.treeSearch(rootNode, logmessageL)

                # Match no existing log cluster
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
                    newCluster.st = 0.5 * (len(logmessageL)-numOfPara) / float(len(logmessageL))
                    newCluster.initst = newCluster.st

                    # When the number of numOfPara is large, the group tends to accept more log messages to generate the template
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

                    if ' '.join(newTemplate) != ' '.join(matchCluster.logTemplate):
                        matchCluster.logTemplate = newTemplate

                        # Update the similarity threshold of current existing cluster
                        matchCluster.updateCount = matchCluster.updateCount + numUpdatedToken
                        matchCluster.st = min( 1, matchCluster.initst + 0.5*math.log(matchCluster.updateCount+1, matchCluster.base) )

                        # If the merge mechanism is used, then merge the nodes
                        # weihan: TBD if I need this feature in ML and Oldshchool
                        if self.para.mt < 1:
                            self.adjustOutputCell(matchCluster, logCluL)


        if not os.path.exists(self.para.savePath):
            os.makedirs(self.para.savePath)
        else:
            self.deleteAllFiles(self.para.savePath)

        self.outputResult(logCluL, outputCeL)
        t2 = time.time()

        print('this process takes',t2-t1)
        print('*********************************************')
        gc.collect()
        return t2-t1
