#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore

from nat.modelingParameter import getParameterTypes
from nat.parameterInstance import ParameterInstance
from nat.paramDesc import ParamDescTrace

from .variableTableWgt import VariableTableView, VariableListModel



class ParamTraceWgt(QtGui.QWidget):

    paramTypeSelected = QtCore.Signal(str)
    
    def __init__(self, parent):
        self.parent = parent
        super(ParamTraceWgt, self).__init__(parent)
        self.parameterTypes = getParameterTypes()

        # Widgets        
        self.varListTblWdg  = VariableTableView(self) 
        self.varListModel   = VariableListModel(self)
        self.varListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.varListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectItems)
        self.varListTblWdg.setModel(self.varListModel)

        selection = self.varListTblWdg.selectionModel()
        selection.selectionChanged.connect(self.varSelectionChanged)
        
        self.varListTblWdg.depTypeSelected.connect(self.newParamSelected)
        
        self.addIndepVarBtn    = QtGui.QPushButton("Add indep. variable")
        self.addDepVarCompBtn  = QtGui.QPushButton("Add a component to the dep. var.")
        self.deleteIndepVarBtn = QtGui.QPushButton("Delete variable")
        self.addSample         = QtGui.QPushButton("Add sample")
        self.deleteSample      = QtGui.QPushButton("Delete sample")
        self.loadCSV           = QtGui.QPushButton("Load CSV")

        self.deleteSample.setDisabled(True)
        self.deleteIndepVarBtn.setDisabled(True)
        
        # Signals
        self.addIndepVarBtn.clicked.connect(self.varListModel.addVariable)
        self.addDepVarCompBtn.clicked.connect(self.varListModel.addDepCompnent)
        self.deleteIndepVarBtn.clicked.connect(self.varListTblWdg.deleteVariable)
        self.addSample.clicked.connect(self.varListModel.addSample)
        self.deleteSample.clicked.connect(self.varListTblWdg.deleteSample)
        self.varListTblWdg.depTypeSelected.connect(self.depVarSelected)

        # Layout
        grid = QtGui.QGridLayout(self)
        grid.addWidget(self.varListTblWdg, 0, 0, 7, 1)
        grid.addWidget(self.addIndepVarBtn, 0, 1)
        grid.addWidget(self.addDepVarCompBtn, 1, 1)
        grid.addWidget(self.deleteIndepVarBtn, 2, 1)
        grid.addWidget(self.addSample, 3, 1)
        grid.addWidget(self.deleteSample, 4, 1)
        grid.addWidget(self.loadCSV, 5, 1)

        self.varListTblWdg.clicked.connect(self.tableClicked)


    def tableClicked(self, index):
        self.varSelectionChanged(index, None)


    def newParamSelected(self, paramType):
        self.paramTypeSelected.emit(paramType)

    def varSelectionChanged(self, selected, deselected):
        #col = self.varListTblWdg.selectionModel().currentIndex().column()

        if isinstance(selected, QtCore.QModelIndex):
            index = selected
        elif isinstance(selected, QtGui.QItemSelection):
            if len(selected.indexes()) == 1:
                index = selected.indexes()[0]
            else:
                return
            
        self.deleteSample.setDisabled(index.row() < 3)
        colName = self.varListModel.colHeader[index.column()]
        nbIndep = self.varListModel.nbIndep
        self.deleteIndepVarBtn.setDisabled(colName == "Dependant" or 
                                           ("Independant" in colName and nbIndep == 1))

        #paramType = self.varListModel.getType(col)
        #if not paramType is None and "Dependant" in colName:
        #    self.paramTypeSelected.emit(paramType)


    @QtCore.Slot(object, str)
    def depVarSelected(self, depVar):
        self.paramTypeSelected.emit(depVar)

    def newParameter(self):
        self.varListModel.clear()

    def saveParameter(self, relationship, paramId):
        depVar        = self.varListModel.getDepVar(varType="NumericalVariable")
        indepVars     = self.varListModel.getIndepVars(varType="NumericalVariable")
        description     = ParamDescTrace(depVar, indepVars)
        return ParameterInstance(paramId, description, [], relationship)


    def loadRow(self, currentParameter):
        if currentParameter is None:
            self.varListModel.clear()            
        else:
            self.varListModel.setFromParam(currentParameter)
            self.varListModel.refresh()

    def loadModelingParameter(self, row = None):
        pass


