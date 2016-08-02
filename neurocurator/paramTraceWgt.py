#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore

from nat.modelingParameter import getParameterTypes, ParameterInstance,  ParamDescTrace

from .variableTableWgt import VariableTableView, VariableListModel


class ParamTraceWgt(QtGui.QWidget):

    paramTypeSelected = QtCore.Signal(str)
    
    def __init__(self, parent):
        super(ParamTraceWgt, self).__init__()
        self.parent = parent
        self.parameterTypes = getParameterTypes()

        # Widgets        
        self.varListTblWdg  = VariableTableView() 
        self.varListModel     = VariableListModel(self)
        self.varListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.varListTblWdg.setModel(self.varListModel)

        self.addIndepVarBtn        = QtGui.QPushButton("Add variable")
        self.deleteIndepVarBtn    = QtGui.QPushButton("Delete variable")
        self.addSample            = QtGui.QPushButton("Add sample")
        self.deleteSample        = QtGui.QPushButton("Delete sample")
        self.loadCSV            = QtGui.QPushButton("Load CSV")

        # Signals
        self.addIndepVarBtn.clicked.connect(self.varListModel.addVariable)
        self.deleteIndepVarBtn.clicked.connect(self.varListTblWdg.deleteVariable)
        self.addSample.clicked.connect(self.varListModel.addSample)
        self.deleteSample.clicked.connect(self.varListTblWdg.deleteSample)
        self.varListTblWdg.depTypeSelected.connect(self.depVarSelected)

        # Layout
        grid     = QtGui.QGridLayout(self)
        grid.addWidget(self.varListTblWdg, 0, 0, 6, 1)
        grid.addWidget(self.addIndepVarBtn, 0, 1)
        grid.addWidget(self.deleteIndepVarBtn, 1, 1)
        grid.addWidget(self.addSample, 2, 1)
        grid.addWidget(self.deleteSample, 3, 1)
        grid.addWidget(self.loadCSV, 4, 1)


    @QtCore.Slot(object, str)
    def depVarSelected(self, depVar):
        self.paramTypeSelected.emit(depVar)

    def newParameter(self):
        self.varListModel.clear()

    def saveParameter(self, relationship, paramId):
        depVar        = self.varListModel.getDepVar(varType="NumericalVariable")
        indepVars     = self.varListModel.getIndepVars(varType="NumericalVariable")
        description     = ParamDescTrace(depVar, indepVars)
        return ParameterInstance(paramId, description, [], [], relationship)

    def loadRow(self, currentParameter):
        self.varListModel.setFromParam(currentParameter)
        self.varListModel.refresh()

    def loadModelingParameter(self, row = None):
        pass


