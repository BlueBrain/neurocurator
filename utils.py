# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 12:12:13 2016

@author: oreilly
"""
from os.path import join
import annotation 

# Records associated with publications are saved with a file name using the ID
# However, ID (e.g., DOI) may contain the forward slash ("/") character which is not allowed
# in file names. It is therefore replaced by the character hereby specified 
# everytime the ID has to be used for naming files.
forwardSlashEncoder = "%2F"



def getParametersForPub(dbPath, pubId):
    fileName = join(dbPath, pubId + ".pcr") 
    with open(fileName, "r", encoding="utf-8", errors='ignore') as f:
        try:
            annotations = annotation.Annotation.readIn(f)
        except ValueError:
            raise ValueError("Problem reading file " + fileName + ". The JSON coding of this file seems corrupted.")

    parameters = []
    for annot in annotations:
        parameters.extend(annot.parameters)
    return parameters




def Id2FileName(ID):
    assert(not forwardSlashEncoder in ID)
    return ID.replace("/", forwardSlashEncoder)

def fileName2Id(fileName):
    assert(not "/" in fileName)
    return fileName.replace(forwardSlashEncoder, "/")