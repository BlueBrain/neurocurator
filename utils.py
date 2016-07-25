# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 12:12:13 2016

@author: oreilly
"""
from os.path import join

# Records associated with publications are saved with a file name using the ID
# However, ID (e.g., DOI) may contain the forward slash ("/") character which is not allowed
# in file names. It is therefore replaced by the character hereby specified 
# everytime the ID has to be used for naming files.
forwardSlashEncoder = "%2F"


def Id2FileName(ID):
    assert(not forwardSlashEncoder in ID)
    return ID.replace("/", forwardSlashEncoder)

def fileName2Id(fileName):
    assert(not "/" in fileName)
    return fileName.replace(forwardSlashEncoder, "/")