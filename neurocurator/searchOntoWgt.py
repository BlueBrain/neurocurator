# -*- coding: utf-8 -*-
"""
Created on Tue Jul 26 10:23:39 2016

@author: oreilly
"""

# Import PySide classes
from PySide import QtGui, QtCore
from sys import platform as _platform
from nat import ontoServ

class OntoAutoComplete(QtGui.QLineEdit):

    completionTermatiated = QtCore.Signal(dict)

    def focusInEvent(self, event):
        if _platform == "linux" or _platform == "linux2":
            # This behavior is the original one, which is fine in linux. On MacOS,
            # selecting an item change the value of the combobox and then set the focus on it
            # which was making this line erase the selected text.
            self.setText("")

        super(OntoAutoComplete, self).focusInEvent(event)

        
    def event(self, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Tab:
                completion = ontoServ.autocomplete(self.text())
                self.completionTermatiated.emit(completion)
                
        return super(OntoAutoComplete, self).event(event)        




class OntoOnlineSearch(QtGui.QWidget):


    tagSelected = QtCore.Signal(str, str)
    
    def __init__(self, *args, **kwargs):
        super(OntoOnlineSearch, self).__init__(*args, **kwargs)

        self.termListTblWdg     = QtGui.QTableView() 
        self.termTableModel     = OntoTermsListModel(self)
        self.termListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.termListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.termListTblWdg.setModel(self.termTableModel)


        self.termListTblWdg.setColumnWidth(0, 300)
        self.termListTblWdg.setColumnWidth(1, 200)

        # Signals
        self.termSelectionModel = self.termListTblWdg.selectionModel()
        self.termSelectionModel.selectionChanged.connect(self.termSelected)
        #self.termTableModel.layoutChanged.connect(self.termTableLayoutChanged)


        self.autoCompleteTxt = OntoAutoComplete(self)
        self.autoCompleteTxt.completionTermatiated.connect(self.completionUpdate)        
        
        grid = QtGui.QGridLayout(self)
        grid.addWidget(self.termListTblWdg, 0, 0)   
        grid.addWidget(self.autoCompleteTxt, 1, 0)



    def termSelected(self, selection, deselected=None):
        #id = [tagId for tagId, tagName in self.dicData.items() if name == tagName]
        #assert(len(id)==1)
        #id = id[0]
        #self.addTagToAnnotation(id)
        #self.tagEdit.erase = True
        #self.tagEdit.clearEditText()
        term = self.termTableModel.getTerm(selection.indexes()[0])
        self.tagSelected.emit(term[0], term[1])


    @QtCore.Slot(object, dict)
    def completionUpdate(self, termDic):
        #print(termDic)
        self.termTableModel.setTerms(termDic)



class OntoTermsListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, terms = [], header = ['term', 'curie'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.terms = terms
        self.header = header
        self.sortCol   = 0 
        self.sortOrder = QtCore.Qt.AscendingOrder        

    def rowCount(self, parent=None):
        return len(self.terms)

    def columnCount(self, parent=None):
        return len(self.header)


    """
    def getSelectedTerm(self, selection):

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
    """


    def getByIndex(self, term, ind):
        return term[ind]


    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        return self.getByIndex(self.terms[index.row()], index.column())

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
        self.annotationList = sorted(self.terms, key=lambda x: self.getByIndex(x, col), reverse = reverse) #operator.itemgetter(col))
        #if order == QtCore.Qt.DescendingOrder:
        #    self.mylist.reverse()
        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def getTerm(self, index):
        return self.terms[index.row()]

    def setTerms(self, termDic):
        self.terms = [(term, curie) for curie, term in termDic.items()]
        self.refresh()
    
    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))

