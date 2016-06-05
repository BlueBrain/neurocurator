# -*- coding: utf-8 -*-
"""
Created on Fri Jun  3 16:48:25 2016

@author: oreilly
"""

import re
import numpy as np
from difflib import SequenceMatcher
from os.path import join, isfile
from restClient import RESTClient 

class AnnotTextLocalizer:
    
    def __init__(self, dbPath, contextLength=50, restServerURL=None):
        self.dbPath        = dbPath
        self.contextLength = contextLength
        if not restServerURL is None:
            self.restClient = RESTClient(restServerURL)
        else:
            self.restClient = None


    def fullTextLocallyAvailable(self, paperId):
        txtFileName = join(self.dbPath, paperId) + ".txt"
        return isfile(txtFileName)
            
        
    def localizeTextAnnot(self, paperId, textToAnnotate):

        if self.fullTextAvailable(paperId):
            return self.localTextLocalization(paperId, textToAnnotate)
        else:
            return self.remoteTextLocalization(paperId, textToAnnotate)
        
            
    def remoteTextLocalization(self, paperId, textToAnnotate):
        if self.restClient is None:
            return None
            
        return self.restClient.localizeAnnotation(paperId, textToAnnotate)
            

    
    def localTextLocalization(self, paperId, textToAnnotate):
        
        def recursiveSearch(queryString, text, a=0, level=0, maxLevel=5):

            starts = [(a, m.start(), len(queryString)) for m in re.finditer(re.escape(queryString), text)]
            if len(starts) == 0:
                if level < maxLevel and len(queryString) > 4:
                    N = len(queryString)
                    starts = []
                    starts.extend(recursiveSearch(queryString[:int(N/2)], text, a,             level+1, maxLevel))
                    starts.extend(recursiveSearch(queryString[int(N/2):], text, a+int(N/2), level+1, maxLevel))
                    return starts
                else:
                    return starts
            else:
                return starts

        def processBlocks(blocks, textToAnnotate, fileText, contextLength):
            for block in blocks:
                matcher = SequenceMatcher(None, textToAnnotate, fileText[block["start"]:block["end"]])
                ratio = matcher.ratio()

                matcher.set_seq2(fileText[block["start"]-1:block["end"]])
                new_ratio = matcher.ratio()
                while new_ratio >= ratio and block["start"] > 0: 
                    block["start"] -= 1
                    ratio = new_ratio
                    matcher.set_seq2(fileText[block["start"]-1:block["end"]])
                    new_ratio = matcher.ratio()

                matcher.set_seq2(fileText[block["start"]+1:block["end"]])
                new_ratio = matcher.ratio()
                while new_ratio >= ratio and block["start"] < len(fileText)-1: 
                    block["start"] += 1
                    ratio = new_ratio
                    matcher.set_seq2(fileText[block["start"]+1:block["end"]])
                    new_ratio = matcher.ratio()

                matcher.set_seq2(fileText[block["start"]:block["end"]-1])
                new_ratio = matcher.ratio()
                while new_ratio >= ratio and block["end"] > 0: 
                    block["end"] -= 1
                    ratio = new_ratio
                    matcher.set_seq2(fileText[block["start"]:block["end"]-1])
                    new_ratio = matcher.ratio()

                matcher.set_seq2(fileText[block["start"]:block["end"]+1])
                new_ratio = matcher.ratio()
                while new_ratio >= ratio and block["end"] < len(fileText)-1: 
                    block["end"] += 1
                    ratio = new_ratio
                    matcher.set_seq2(fileText[block["start"]:block["end"]+1])
                    new_ratio = matcher.ratio()


                block["contextBefore"]    = fileText[max(0, block["start"]-contextLength):block["start"]]
                block["candidate"]        = fileText[block["start"]:block["end"]]
                block["contextAfter"]     = fileText[block["end"]:min(len(fileText), block["end"]+contextLength)]
                block["ratio"]            = ratio
                block["candidate"]        = block["candidate"].replace("\n", " ")        

            return np.array([block for block in blocks if block["ratio"] > 0.5])



        txtFileName = join(self.dbPath, paperId) + ".txt"
        with open(txtFileName, 'r', encoding="utf-8", errors='ignore') as f :
            fileText = f.read()

        ## We try to find an exact match...
        starts = [m.start() for m in re.finditer(re.escape(textToAnnotate), fileText)]

        ## If no exact match was found...        
        if len(starts) == 0:

            N = len(textToAnnotate)

            ## We try to find partial matches using a recursive algorithm that sequentially
            ## splits the query string and try to find these subsetrings
            blocks = []
            for a, b, size in recursiveSearch(textToAnnotate, fileText):
                start = max(0, b-a)
                blocks.append({"start":start,
                               "end"  :min(start+N, len(fileText))})
            blocks = processBlocks(blocks, textToAnnotate, fileText, self.contextLength)

            u, indices = np.unique([str(block["start"]) + "-" + str(block["end"]) for block in blocks], return_index=True)
            blocks = blocks[indices]
            blocks = sorted(blocks, key=lambda match: match["ratio"], reverse=True)

        elif len(starts) == 1:
            start = starts[0]        
            end   = start+N
            block = {"start":start, "end":end, "candidate":textToAnnotate}       
            block["contextBefore"]    = fileText[max(0, start-self.contextLength):start]
            block["contextAfter"]     = fileText[end:min(len(fileText), end+self.contextLength)]
            blocks = [block]
        else:
            blocks = [{"start"        : m.start(), 
                       "end"          : m.start()+N, 
                       "contextBefore": fileText[max(0, m.start()-self.contextLength):m.start()],
                       "contextAfter" : fileText[(m.start()+N):min(len(fileText), m.start()+N+self.contextLength)],
                       "candidate"    : textToAnnotate} 
                       for m in re.finditer(self.textToAnnotateTxt.text(), fileText)]         
      
        return blocks
                       
                       
                       
                       
                       
                       
                       
                  

