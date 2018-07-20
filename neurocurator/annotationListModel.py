# -*- coding: utf-8 -*-
"""
Created on Mon Jun 20 16:23:49 2016

@author: oreilly
"""

from PyQt5.QtCore import Qt, QModelIndex, QItemSelection, QAbstractTableModel


class AnnotationListModel(QAbstractTableModel):

    def __init__(self, annotationList = [], header = ['ID', 'type', 'localizer', 'comment'], parent=None):
        super().__init__(parent)
        self.annotationList = annotationList
        self.header = header
        self.nbCol = len(header)
        self.sortCol   = 0 
        self.sortOrder = Qt.AscendingOrder

    def rowCount(self, parent=QModelIndex()):
        return len(self.annotationList)

    def columnCount(self, parent=QModelIndex()):
        return self.nbCol 

    def getSelectedAnnotation(self, selected):
        # FIXME Delayed refactoring. Different entry points with different types.
        if isinstance(selected, QItemSelection):
            selected = selected.indexes()

        # At this stage, selected is a QModelIndexList in both cases.
        if selected:
            index = selected[0]
            try:
                return self.annotationList[index.row()]
            except IndexError:
                # FIXME Delayed refactoring. The selection has not been properly
                # cleared (annotation deletion).
                return None
        else:
            return None

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

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        return self.getByIndex(self.annotationList[index.row()], index.column())

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col=None, order=None):
        if col is None:
            col = self.sortCol 
        if order is None:
            order = self.sortOrder

        # Sort table by given column number col.
        self.layoutAboutToBeChanged.emit()

        reverse = (order == Qt.DescendingOrder)
        self.annotationList = sorted(self.annotationList, key=lambda x: self.getByIndex(x, col), reverse = reverse) #operator.itemgetter(col))
        #if order == Qt.DescendingOrder:
        #    self.mylist.reverse()

        self.layoutChanged.emit()

    def refresh(self):
        self.layoutChanged.emit()
