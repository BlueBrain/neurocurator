# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 12:12:13 2016

@author: oreilly
"""
from os.path import join

from annotation import Annotation

def getParametersForPub(dbPath, pubId):
    fileName = join(dbPath, pubId + ".pcr") 
    with open(fileName, "r", encoding="utf-8", errors='ignore') as f:
        try:
            annotations = Annotation.readIn(f)
        except ValueError:
            raise ValueError("Problem reading file " + fileName + ". The JSON coding of this file seems corrupted.")

    parameters = []
    for annot in annotations:
        parameters.extend(annot.parameters)
    return parameters
