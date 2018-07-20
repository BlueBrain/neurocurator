#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import numpy as np
import pandas as pd
from PyQt5.QtCore import QModelIndex, pyqtSignal, pyqtSlot, Qt, QAbstractTableModel
from PyQt5.QtWidgets import (QTableView, QCheckBox, QVBoxLayout, QWidget,
                             QHBoxLayout, QGroupBox, QComboBox, QLineEdit,
                             QFileDialog, QSplitter, QPushButton,
                             QAbstractItemView, QHeaderView)

from nat.annotationSearch import (parameterKeys, annotationKeys,
                                  ParameterSearch,
                                  AnnotationSearch, parameterResultFields,
                                  annotationResultFields)
from nat.condition import ConditionAtom, ConditionAND, ConditionOR, ConditionNOT
from nat.ontoManager import OntoManager
from .autocomplete import AutoCompleteEdit
from .itemDelegates import ParamTypeCbo, CheckBoxDelegate


class SearchWgt(QWidget):

    annotationSelected = pyqtSignal(object)
    parameterSelected  = pyqtSignal(object, object)

    def __init__(self, searchType="Parameter", parent=None):
        super().__init__(parent)

        # FIXME Delayed refactoring.
        self._parent         = parent

        self.searchType     = searchType
        self.queryDef       = QueryDefinitionWgt(searchType, self)
        self.outputFormat   = OutputFormatWgt(searchType, self)
        
        self.view = QTableView()
        self.view.setWordWrap(True)
        self.view.setTextElideMode(Qt.ElideMiddle)
        self.view.resizeRowsToContents()
        self.view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        self.model = PandasModel()
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)

        self.view.setModel(self.model)

        self.buttonWgt  = QWidget(self)
        buttonLayout    = QHBoxLayout(self.buttonWgt)
        self.searchBtn  = QPushButton("Search", self)
        self.saveBtn    = QPushButton("Save as .csv", self)
        buttonLayout.addWidget(self.searchBtn)
        buttonLayout.addWidget(self.saveBtn)
        
        self.searchBtn.clicked.connect(self.search)  
        self.saveBtn.clicked.connect(self.saveResults)   
        self.view.doubleClicked.connect(self.loadItem)

        self.splitter = QSplitter(Qt.Vertical, self)
        
        self.splitter.addWidget(self.queryDef)
        self.splitter.addWidget(self.outputFormat)
        self.splitter.addWidget(self.view)
        self.splitter.addWidget(self.buttonWgt)    
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)

    def loadItem(self, index):
        if self.searchType == "Parameter":
            parameter  = self.model.getObject(index, "obj_parameter")
            annotation = self.model.getObject(index, "obj_annotation")
            self.parameterSelected.emit(annotation, parameter)

        elif self.searchType == "Annotation":
            annotation = self.model.getObject(index, "obj_annotation")
            self.annotationSelected.emit(annotation)
        else:
            raise ValueError

        
    def search(self):        

        if self._parent is None:
            dbPath = None
        elif not hasattr(self._parent, "dbPath"):
            dbPath = None
        else:
            dbPath = self._parent.dbPath

        if self.searchType == "Parameter":
            searcher = ParameterSearch(dbPath)
        elif self.searchType == "Annotation":
            searcher = AnnotationSearch(dbPath)
        else:
            raise ValueError

        query = self.queryDef.getQuery()
        if not query is None:
            searcher.setSearchConditions(query)
        searcher.setResultFields(self.outputFormat.getFields())
        self.outputFormat.setSearcherProperties(searcher)
            
        result = searcher.search()
        self.model._data = result
        self.model.refresh()
        
    def saveResults(self):
        
        fname, _ = QFileDialog.getSaveFileName(self, 'Save research results')
        if not fname == "":
            if not "." in fname:
                fname = fname + ".csv"
            self.model._data.to_csv(fname)


class QueryDefinitionWgt(QGroupBox):

    def __init__(self, searchType, parent=None):
        super().__init__("Search conditions", parent)
        self.searchType = searchType
        self.node = QueryNodeWgt(self.searchType, self)       
        layout = QVBoxLayout(self)
        layout.addWidget(self.node)
        layout.addStretch(100)
        
    def getQuery(self):
        return self.node.getQuery()
    

class QueryNodeWgt(QWidget):

    valueTypeChanged = pyqtSignal(object, object)

    def __init__(self, searchType, parent=None):
        super().__init__(parent)
        self.conditionTypeCbo = QComboBox(self)
        self.rowsWgt          = QWidget(self)
        self.conditionTypeCbo.addItems(["", "AND", "OR", "NOT"])
        self.searchType = searchType
        self.queryRows  = []
        layout = QHBoxLayout(self)
        layout.addWidget(self.conditionTypeCbo)
        layout.addWidget(self.rowsWgt)
        self.rowsLayout = QVBoxLayout(self.rowsWgt)
        self.addARow()
        self.conditionTypeCbo.currentIndexChanged.connect(self.conditionTypeChanged)

    def getQuery(self):
        query = None
        if self.conditionTypeCbo.currentText() == "":
            if not (self.rowsLayout.count() == 1 and isinstance(self.queryRows[0], QueryRowWgt)):
                raise ValueError
            query = self.queryRows[0].getQuery()

        elif self.conditionTypeCbo.currentText() == "NOT":
            if not (self.rowsLayout.count() == 1 and isinstance(self.queryRows[0], QueryRowWgt)):
                raise ValueError
            query = self.queryRows[0].getQuery()
            if not query is None:
                query = ConditionNOT(query)

        elif self.conditionTypeCbo.currentText() == "AND": 
            query = [row.getQuery() for row in self.queryRows if not row.getQuery() is None]
            if len(query):
                query = ConditionAND(query)
                    
        elif self.conditionTypeCbo.currentText() == "OR": 
            query = [row.getQuery() for row in self.queryRows if not row.getQuery() is None]
            if len(query):
                query = ConditionOR(query)
            
        else:
            raise ValueError        
        
        return query
        
    def conditionTypeChanged(self):
        if self.conditionTypeCbo.currentText() in ["", "NOT"]:
            if not (self.rowsLayout.count() == 1 and isinstance(self.queryRows[0], QueryRowWgt)):
                self.clear()
                self.addARow()
                
        elif self.conditionTypeCbo.currentText() in ["AND", "OR"]: 
            if isinstance(self.queryRows[0], QueryRowWgt):
                self.clear()
                self.addANode()            
        else:
            raise ValueError


    def clear(self):
        while self.rowsLayout.count():
            child = self.rowsLayout.takeAt(0)
            child.widget().deleteLater()
        self.queryRows = []

        
    def addARow(self):
        rowWgt = QueryRowWgt(self.searchType, self)
        self.queryRows.append(rowWgt)
        self.rowsLayout.addWidget(rowWgt)   
        rowWgt.valueTypeChanged.connect(self.valueTypeChangedSlot)

    def addANode(self):
        nodeWgt = QueryNodeWgt(self.searchType, self)
        self.queryRows.append(nodeWgt)
        self.rowsLayout.addWidget(self.queryRows[-1])
        nodeWgt.valueTypeChanged.connect(self.valueTypeChangedSlot)

    @pyqtSlot(object)
    @pyqtSlot(object, object)
    def valueTypeChangedSlot(self, rowObject, nodeObject=None):
        if self.conditionTypeCbo.currentText() in ["", "NOT"]:
            self.valueTypeChanged.emit(rowObject, self)
        else:
            noRow = self.queryRows.index(nodeObject)
            if rowObject.valueType.currentText() == "" and self.rowsLayout.count() > 1 :
                child = self.rowsLayout.takeAt(noRow)
                child.widget().deleteLater()    
                del self.queryRows[noRow]
            elif rowObject.valueType.currentText() != "" and noRow == self.rowsLayout.count()-1 :
                #if self.conditionTypeCbo.currentText() in ["AND", "OR"]:
                self.addANode()


class QueryRowWgt(QWidget):

    valueTypeChanged = pyqtSignal(object)
    
    ontoMng  = OntoManager()
    treeData = ontoMng.trees 
    dicData  = ontoMng.dics

    tagNames  = np.array(list(dicData.values()))      
    del dicData
    del treeData    
    
    def __init__(self, searchType, parent=None):
        super().__init__(parent)
        
        self.searchType = searchType
        self.valueType  = QComboBox(self)
        self.valueType.addItem("")

        if self.searchType == "Annotation":
            self.valueType.addItems(annotationKeys)    
        elif self.searchType == "Parameter":
            self.valueType.addItems(parameterKeys)    
        else:
            raise ValueError()
            
        self.valueType.currentIndexChanged.connect(self.valueTypeChangedEmit)
        
        self.value      = QLineEdit(self)
        self.value.setEnabled(False)

        self.layout = QHBoxLayout(self)
        self.layout.addWidget(self.valueType)
        self.layout.addWidget(self.value)

    def valueTypeChangedEmit(self):
        self.value.setEnabled(self.valueType.currentText() != "")            

        child = self.layout.takeAt(1)
        child.widget().deleteLater()    
        if self.valueType.currentText() == "Has parameter":
            self.value = QComboBox(self)
            self.value.addItems(["False", "True"])
        elif self.valueType.currentText() == "Annotation type":
            self.value = QComboBox(self)
            self.value.addItems(["text", "figure", "table", "equation", "position"])
        elif self.valueType.currentText() == "Parameter name":
            self.value = ParamTypeCbo(self)
        elif self.valueType.currentText() in ["Tag name", "Required tag name"]:
            self.value = AutoCompleteEdit(self)
            self.value.setModel(QueryRowWgt.tagNames)                        
        elif self.valueType.currentText() == "Result type":
            self.value = QComboBox(self)
            self.value.addItems(["pointValue", "function", "numericalTrace"])
        else:
            self.value = QLineEdit(self)
 
        self.layout.addWidget(self.value)
        self.valueTypeChanged.emit(self)
        


    def getQuery(self):
        if self.valueType.currentText() == "":
            return None
            
        if isinstance(self.value, QLineEdit):
            value = self.value.text()
        elif isinstance(self.value, QComboBox):
            value = self.value.currentText()
        else:
            raise TypeError
            
        return ConditionAtom(self.valueType.currentText(), value)


class OutputFormatWgt(QGroupBox):

    def __init__(self, searchType, parent=None):
        super().__init__("Output format", parent)

        self.searchType = searchType

        if self.searchType == "Parameter":
            self.fields = parameterResultFields
        elif self.searchType == "Annotation":
            self.fields = annotationResultFields
        else:
            raise ValueError

        self.fieldsTblWdg       = FieldTableView(self)
        self.paramListModel     = FieldListModel(parent=self)
        #self.paramListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        #self.paramListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.fieldsTblWdg.setModel(self.paramListModel)
        self.fieldsTblWdg.setColumnWidth(0, 30)
        self.fieldsTblWdg.setColumnWidth(1, 200)

        self.outputProperties = OutputPropertiesWgt(searchType, self)

        layout = QHBoxLayout(self)
        layout.addWidget(self.fieldsTblWdg)
        layout.addWidget(self.outputProperties)
        
        self.paramListModel.load(self.fields)
    
    def getFields(self):
        return self.paramListModel.getSelectedFields()

    def setSearcherProperties(self, searcher):
        self.outputProperties.setSearcherProperties(searcher)


class OutputPropertiesWgt(QWidget):

    def __init__(self, searchType, parent=None):
        super().__init__(parent)

        self.searchType = searchType

        layout = QVBoxLayout(self)

        if self.searchType == "Parameter":
            self.expandRequiredTagsChk  = QCheckBox("Expand required tags")
            self.onlyCentralTendancyChk = QCheckBox("Show only central tendency of parameter values")
            layout.addWidget(self.onlyCentralTendancyChk)
            layout.addWidget(self.expandRequiredTagsChk)
            layout.addStretch(1)
            
        elif self.searchType == "Annotation":
            pass
        
        else:
            raise ValueError

    def setSearcherProperties(self, searcher):

        if self.searchType == "Parameter":
            searcher.expandRequiredTags  = self.expandRequiredTagsChk.isChecked()
            searcher.onlyCentralTendancy = self.onlyCentralTendancyChk.isChecked()
            
        elif self.searchType == "Annotation":
            pass
        
        else:
            raise ValueError


class PandasModel(QAbstractTableModel):

    def __init__(self, data=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._data = data

    def rowCount(self, parent=QModelIndex()):
        return len(self._data.values)

    def columns(self):
        return [col for col in self._data.columns if col[:4] != "obj_"] 
        
    def indDisplayColumns(self):
        return [no for no, col in enumerate(self._data.columns) if col[:4] != "obj_"] 

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns())

    def data(self, index, role= Qt.DisplayRole):
        if index.isValid():
            if role == Qt.DisplayRole:
                return str(self._data.values[index.row()][self.indDisplayColumns()[index.column()]])
        return None

    def getObject(self, index, objField):
        for col in self._data.columns:
            if col == objField: 
                return self._data[objField][index.row()]
        raise ValueError

    def headerData(self, index, orientation, role=Qt.DisplayRole):
        if   orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.columns()[index]
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return str(self._data.index[index])
        return None


    def refresh(self):
        self.layoutChanged.emit()


class FieldTableView(QTableView):

    tableCheckBoxClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegateForColumn(0, CheckBoxDelegate(self))      

    @pyqtSlot(bool)
    def checkBoxClicked(self, clicked):
        self.model().toggleParameter(self.sender().row)
        self.tableCheckBoxClicked.emit(self.sender().row)


class FieldListModel(QAbstractTableModel):

    def __init__(self, colHeader = ['', 'Fields to include'], parent=None): #'Type',
        super().__init__(parent)

        #self.parameterList = parameterList
        self.colHeader = colHeader
        self.nbCol     = len(colHeader)
        #self.types       = []
        self.fields    = []
        self.selected  = []

    #def clear(self):
    #    for id in self.selected:
    #        self.selected[id] = False
    #    self.refresh()

    def rowCount(self, parent=QModelIndex()):
        return len(self.fields)

    def columnCount(self, parent=QModelIndex()):
        return self.nbCol 


    def getByIndex(self, row, col):
        if col == 0:
            return self.selected[row]
        elif col == 1:
            return self.fields[row]
        else:
            raise ValueError


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        return self.getByIndex(index.row(), index.column())


    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled



    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.colHeader[section]        
        return None


    def load(self, fields):
        self.fields = fields
        self.selected = [True]*len(fields)
        self.refresh()

        
    def selectParameter(self, row, selected):
        self.selected[row] = selected

    def toggleParameter(self, row):
        self.selected[row] = not self.selected[row]

    def refresh(self):
        self.layoutChanged.emit()

    def getSelectedFields(self):
        return [field for field, selected in zip(self.fields, self.selected) if selected]

