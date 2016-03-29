#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore

#from modelingParameter import ExperimentProperty
#from itemDelegates import ExpPropertiesDelegate
from paramFunctionWgt import ParameterInstanceTableView, ParameterInstanceListModel
from utils import getParametersForPub
from modelingParameter import ParamRef



"""
class ExpPropertiesTableView(QtGui.QTableView):

    def __init__(self, *args, **kwargs):
        QtGui.QTableView.__init__(self, *args, **kwargs)
        self.setItemDelegateForColumn(0, ExpPropertiesDelegate(self))



class ExpPropertiesListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, colHeader = ['Property', 'Value', 'Unit'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.colHeader             = colHeader
        self.nbCol                 = len(colHeader)
        self.expPropertyList        = [] 

    def clear(self):
        self.expPropertyList     = [] 
        self.refresh()

    def rowCount(self, parent=None):
        return len(self.expPropertyList)

    def columnCount(self, parent=None):
        return self.nbCol 

    def addProperty(self, name, value, unit):
        self.expPropertyList.append(ExperimentProperty(name, value, unit))
        self.refresh()

    def newRow(self):
        self.addProperty("Temperature", 21.0, "degC")

    def deleteRow(self, selectedRow):
        if selectedRow >= 0 and selectedRow < len(self.expPropertyList):
            del self.expPropertyList[selectedRow]
            self.refresh()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        if index.column() == 0:
            return self.expPropertyList[index.row()].name
        elif index.column() == 1:
            return self.expPropertyList[index.row()].value
        elif index.column() == 2:
            return self.expPropertyList[index.row()].unit
        else:
            raise ValueError


    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if value is None:
            value = ""

        if index.column() == 0:
            self.expPropertyList[index.row()].name    = value
        elif index.column() == 1:
            self.expPropertyList[index.row()].value    = value
        elif index.column() == 2:
            self.expPropertyList[index.row()].unit    = value
        else:
            raise ValueError


    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.colHeader[section]        
        return None

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def getExpProperties(self):
        return self.expPropertyList
      





class ExpPropWgt(QtGui.QWidget):

    def __init__(self, parent):

        self.parent = parent
        super(ExpPropWgt, self).__init__()

        # Widgets    
        self.expPropertiesListTblWdg      = ExpPropertiesTableView() 
        self.expPropertiesListModel       = ExpPropertiesListModel(self)
        self.expPropertiesListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.expPropertiesListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.expPropertiesListTblWdg.setModel(self.expPropertiesListModel)

        self.expPropertiesListTblWdg.setColumnWidth(0, 200)
        self.expPropertiesListTblWdg.setColumnWidth(1, 200)
        self.expPropertiesListTblWdg.setColumnWidth(2, 200)

        self.newExpPropBtn            = QtGui.QPushButton("New")
        self.deleteExpPropBtn         = QtGui.QPushButton("Delete")


        # Signals
        self.newExpPropBtn.clicked.connect(self.newExpProperty)
        self.deleteExpPropBtn.clicked.connect(self.deleteExpProperty)

        self.expPropSelectionModel = self.expPropertiesListTblWdg.selectionModel()
        self.expPropSelectionModel.currentRowChanged.connect(self.expPropertyIndexChanged)


        # Layout        
        expPropertyBtnWgt    = QtGui.QWidget(self)
        expPropertyBtnLayout = QtGui.QVBoxLayout(expPropertyBtnWgt)
        expPropertyBtnLayout.addWidget(self.deleteExpPropBtn)
        expPropertyBtnLayout.addWidget(self.newExpPropBtn)
        expPropertyBtnLayout.addStretch()

        expPropertiesLayout = QtGui.QHBoxLayout(self)
        expPropertiesLayout.addWidget(self.expPropertiesListTblWdg)
        expPropertiesLayout.addWidget(expPropertyBtnWgt)

        # Initial behavior
        self.deleteExpPropBtn.setEnabled(False)


    def expPropertyIndexChanged(self, selected=None, deselected=None):
        self.deleteExpPropBtn.setDisabled(selected.row() == -1)


    def newExpProperty(self):
        self.expPropertiesListModel.newRow()

    def deleteExpProperty(self):
        selectedRow = self.expPropertiesListTblWdg.selectionModel().currentIndex().row()
        self.expPropertiesListModel.deleteRow(selectedRow)
        self.expPropertyIndexChanged(self.expPropertiesListTblWdg.selectionModel().currentIndex())
"""  








class ExpPropWgt(QtGui.QWidget):

    def __init__(self, parent):

        self.parent = parent
        super(ExpPropWgt, self).__init__()

        # Widgets
        self.expPropertiesListTblWdg      = ParameterInstanceTableView() 
        self.expPropertiesListModel       = ParameterInstanceListModel(self)
        self.expPropertiesListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.expPropertiesListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.expPropertiesListTblWdg.setModel(self.expPropertiesListModel)

        self.expPropertiesListTblWdg.setColumnWidth(0, 20)
        self.expPropertiesListTblWdg.setColumnWidth(1, 150)
        self.expPropertiesListTblWdg.setColumnWidth(2, 500)


        # Signal
        self.expPropertiesListTblWdg.tableCheckBoxClicked.connect(self.propSelectionChanged)

        # Layout        
        expPropertiesLayout = QtGui.QHBoxLayout(self)
        expPropertiesLayout.addWidget(self.expPropertiesListTblWdg)


    def fillingExpPropList(self, checkAll=False):
        if self.parent.currentAnnotation is None:      
            return
            
        parameters = getParametersForPub(self.parent.dbPath, self.parent.Id2FileName(self.parent.currentAnnotation.pubId))
        parameters = [param for param in parameters if param.isExperimentProperty == True]

        if checkAll:
            selectedParams = [param.id for param in parameters]  
        elif self.parent.currentAnnotation is None:
            selectedParams = []      
        else:
            selectedParams = [ref.instanceId for ref in self.parent.currentAnnotation.experimentProperties]                  
            
        self.expPropertiesListModel.load(parameters, selectedParams)
        self.expPropertiesListModel.refresh()
        

    def getExpProperties(self):
        parameters = []
        for noRow in range(self.expPropertiesListModel.rowCount()):
            paramInstanceId = self.expPropertiesListModel.getParamInstanceID(noRow)
            if self.expPropertiesListModel.selected[paramInstanceId]:
                parameters.append(ParamRef(paramInstanceId, 
                                       self.expPropertiesListModel.getParamTypeID(noRow)))
        return parameters

    def propSelectionChanged(self, row):
        self.parent.setNeedSaving()

