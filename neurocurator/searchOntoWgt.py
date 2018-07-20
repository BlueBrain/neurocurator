# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 10:23:39 2016

@author: oreilly
"""

from sys import platform as _platform

from PyQt5.QtCore import (QModelIndex, pyqtSignal, pyqtSlot, QAbstractTableModel,
                          QEvent, Qt)
from PyQt5.QtWidgets import (QGridLayout, QAbstractItemView, QTableView, QWidget,
                             QLineEdit)

from nat import ontoServ


class OntoAutoComplete(QLineEdit):

    completionTerminated = pyqtSignal(dict)

    def focusInEvent(self, event):
        if _platform == "linux" or _platform == "linux2":
            # This behavior is the original one, which is fine in linux. On MacOS,
            # selecting an item change the value of the combobox and then set the focus on it
            # which was making this line erase the selected text.
            self.setText("")

        super().focusInEvent(event)

        
    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Tab:
                completion = ontoServ.autocomplete(self.text())
                self.completionTerminated.emit(completion)
                
        return super().event(event)


class OntoOnlineSearch(QWidget):

    tagSelected = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.termListTblWdg = QTableView()
        self.termTableModel = OntoTermsListModel(parent=self)
        self.termListTblWdg.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.termListTblWdg.setSelectionMode(QAbstractItemView.SingleSelection)
        self.termListTblWdg.setModel(self.termTableModel)

        self.termListTblWdg.setColumnWidth(0, 300)
        self.termListTblWdg.setColumnWidth(1, 200)

        # Signals
        self.termSelectionModel = self.termListTblWdg.selectionModel()
        self.termSelectionModel.selectionChanged.connect(self.termSelected)
        #self.termTableModel.layoutChanged.connect(self.termTableLayoutChanged)

        self.autoCompleteTxt = OntoAutoComplete(self)
        self.autoCompleteTxt.completionTerminated.connect(self.completionUpdate)
        
        grid = QGridLayout(self)
        grid.addWidget(self.termListTblWdg, 0, 0)   
        grid.addWidget(self.autoCompleteTxt, 1, 0)

    def termSelected(self, selection, deselected=None):
        #id = [tagId for tagId, tagName in self.dicData.items() if name == tagName]
        #assert(len(id)==1)
        #id = id[0]
        #self.addTagToAnnotation(id)
        #self.tagEdit.erase = True
        #self.tagEdit.clearEditText()
        if len(selection.indexes()):
            term = self.termTableModel.getTerm(selection.indexes()[0])
            self.tagSelected.emit(term[0], term[1])
    
            # Unselect selected item in the table view.
            #self.termListTblWdg.setCurrentCell(-1,-1)
            self.termListTblWdg.clearSelection()
            self.termTableModel.refresh()

    @pyqtSlot(dict)
    def completionUpdate(self, termDic):
        #print(termDic)
        self.termTableModel.setTerms(termDic)


class OntoTermsListModel(QAbstractTableModel):

    def __init__(self, terms = [], header = ['term', 'curie'], parent=None):
        super().__init__(parent)
        self.terms = terms
        self.header = header
        self.sortCol   = 0 
        self.sortOrder = Qt.AscendingOrder

    def rowCount(self, parent=QModelIndex()):
        return len(self.terms)

    def columnCount(self, parent=QModelIndex()):
        return len(self.header)


    """
    def getSelectedTerm(self, selection):

        if isinstance(selection, list):
            if selection == []:
                return None
            elif isinstance(selection[0], QModelIndex):
                index = selection[0]
        else:
            if selection.at(0) is None:
                return None
            index = selection.at(0).indexes()[0]
        return self.annotationList[index.row()]
    """


    def getByIndex(self, term, ind):
        return term[ind]


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        return self.getByIndex(self.terms[index.row()], index.column())

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
        self.annotationList = sorted(self.terms, key=lambda x: self.getByIndex(x, col), reverse = reverse) #operator.itemgetter(col))
        #if order == Qt.DescendingOrder:
        #    self.mylist.reverse()
        self.layoutChanged.emit()

    def getTerm(self, index):
        return self.terms[index.row()]

    def setTerms(self, termDic):
        self.terms = [(term, curie) for curie, term in termDic.items()]
        self.refresh()
    
    def refresh(self):
        self.layoutChanged.emit()
