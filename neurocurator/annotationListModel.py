# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 16:23:49 2016

@author: oreilly
"""

from PySide import QtCore

class AnnotationListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, annotationList = [], header = ['ID', 'type', 'localizer', 'comment'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.annotationList = annotationList
        self.header = header
        self.nbCol = len(header)
        self.sortCol   = 0 
        self.sortOrder = QtCore.Qt.AscendingOrder        

    def rowCount(self, parent=None):
        return len(self.annotationList)

    def columnCount(self, parent=None):
        return self.nbCol 


    def getSelectedAnnotation(self, selection):

        if isinstance(selection, list):
            if selection == []:
                return None
            elif isinstance(selection[0], QtCore.QModelIndex):
                index = selection[0]
        else:
            if selection.at(0) is None:
                return None
            index = selection.at(0).indexes()[0]
        return self.annotationList[index.row()]



    def getByIndex(self, annot, ind):
        if ind == 0:
            return annot.ID
        elif ind == 1:
            return str(annot.type)
        elif ind == 2:
            return str(annot.localizer)
        elif ind == 3 :
            return annot.comment
        else:
            raise ValueError

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        return self.getByIndex(self.annotationList[index.row()], index.column())

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
        self.annotationList = sorted(self.annotationList, key=lambda x: self.getByIndex(x, col), reverse = reverse) #operator.itemgetter(col))
        #if order == QtCore.Qt.DescendingOrder:
        #    self.mylist.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))


