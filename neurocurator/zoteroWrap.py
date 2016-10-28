#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PySide import QtGui, QtCore

import re
import pickle
from dateutil.parser import parse
from pyzotero import zotero
import os

from nat.zoteroWrap import ZoteroWrap

class ZoteroTableModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, checkIdFct, header = ['ID', 'Title', 'Creator', 'Year', 'Journal'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)

        self.header = header
        self.fields = {0:"ID", 1:"title", 2:"creators", 3:"Year", 4:"publicationTitle"}
        self.checkIdFct = checkIdFct
        self.sortCol   = 0 
        self.sortOrder = QtCore.Qt.AscendingOrder
        self.zotWrap   = ZoteroWrap() 


    def loadCachedDB(self, libraryId, libraryrType, apiKey):
        self.zotWrap.loadCachedDB(libraryId, libraryrType, apiKey)

    def refreshDB(self, libraryId, libraryrType, apiKey):
        self.zotWrap.refreshDB(libraryId, libraryrType, apiKey)

    def getID(self, row):
        return self.zotWrap.getID(row)

    def getID_fromRef(self, ref):
        return self.zotWrap.getID_fromRef(ref)

    def getDOI(self, row):
        return self.zotWrap.getDOI(row)

    def getDOI_fromRef(self, ref):
        return self.zotWrap.getDOI_fromRef(ref)

    def getPMID(self, row):
        return self.zotWrap.getPMID(row)        

    def getPMID_fromRef(self, ref):
        return self.zotWrap.getPMID_fromRef(ref)      


    def rowCount(self, parent = None):
        return len(self.zotWrap.refList)

    def columnCount(self, parent = None):
        return len(self.header)


    def getByIndex(self, ref, ind):

        try:
            ###################### CREATORS
            if self.fields[ind] == "creators":
                authors = []
                for creator in ref["creators"]:
                    if creator["creatorType"] == "author":
                        authors.append(creator["lastName"])
                
                # Academic books published as a collection of chapters contributed
                # by different authors have editors but not authors at the level
                # of the book (as opposed to the level of a chapter).
                if len(authors) == 0 and ref['itemType'] == 'book':
                    for creator in ref["creators"]:
                        if creator["creatorType"] == "editor":
                            authors.append(creator["lastName"]) 
                            
                return ", ".join(authors)

            ####################### ID
            elif self.fields[ind] == "ID":
                return self.getID_fromRef(ref)
    
            ####################### YEAR
            elif self.fields[ind] == "Year":
                if ref["date"] == "":
                    return ""
                else:
                    try:
                        return str(parse(ref["date"]).year)
                    except ValueError:
                        return re.search(r'[12]\d{3}', ref["date"]).group(0)

            ####################### PUBLICATIONTITLE
            elif self.fields[ind] == "publicationTitle":
                if ref['itemType'] == 'book':
                    return "book"
                else:
                    return ref[self.fields[ind]]
                

            return ref[self.fields[ind]]
        except KeyError:
            return ""


    def data(self, index, role):
        if not index.isValid():
            return None


        if role == QtCore.Qt.BackgroundRole:
            if self.checkIdFct(self.getID(index.row())) == 2 :
                #color = QtGui.QColor(215, 214, 213)
                color = QtGui.QColor(191, 237, 135)
                return QtGui.QBrush(color, QtCore.Qt.SolidPattern)
            elif self.checkIdFct(self.getID(index.row())) == 1 :
                color = QtGui.QColor(150, 150, 150)
                return QtGui.QBrush(color, QtCore.Qt.SolidPattern)                
            else:
                return None

        if role == QtCore.Qt.DisplayRole:
            try:
                return self.getByIndex(self.zotWrap.refList[index.row()], index.column())
            except KeyError:
                return ""
            

        return None


    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None


    def sort(self, col=None, order=None):
        if col is None:
            col = self.sortCol 
        if order is None:
            order = self.sortOrder

        """sort table by given column number col"""
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        reverse = (order == QtCore.Qt.DescendingOrder)
        self.zotWrap.refList = sorted(self.zotWrap.refList, key=lambda x: self.getByIndex(x, col), reverse = reverse)
        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))

