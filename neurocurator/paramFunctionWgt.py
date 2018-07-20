#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtCore import (QModelIndex, pyqtSignal, pyqtSlot, Qt, QAbstractTableModel)
from PyQt5.QtWidgets import (QTableView, QMessageBox, QLabel, QGridLayout,
                             QTabWidget, QLineEdit, QAbstractItemView, QWidget,
                             QPushButton)

from nat.annotation import getParametersForPub
from nat.modelingParameter import (getParameterTypes, ParameterTypeTree,
                                   getParameterTypeNameFromID)
from nat.paramDesc import ParamDescFunction, InvalidEquation, ParamRef
from nat.parameterInstance import ParameterInstance
from nat.utils import Id2FileName
from .itemDelegates import CheckBoxDelegate
from .variableTableWgt import VariableTableView, VariableListModel


parameterTypeTree = ParameterTypeTree.load()
parameterTypes = getParameterTypes()


class ParamFunctionWgt(QWidget):

    paramTypeSelected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self._parent = parent

        self.parameterTypes = getParameterTypes()

        # Widgets        
        self.addIndepVarBtn = QPushButton("Add variable")
        self.deleteIndepVarBtn = QPushButton("Delete variable")
        self.varListTblWdg = VariableTableView()
        self.varListModel = VariableListModel(parent=self)
        self.varListTblWdg.setSelectionMode(QAbstractItemView.SingleSelection)
        self.varListTblWdg.setModel(self.varListModel)

        self.varTab                = QWidget(self)
        grid                       = QGridLayout(self.varTab)
        grid.addWidget(self.varListTblWdg, 0, 0, 3, 1)
        grid.addWidget(self.addIndepVarBtn, 0, 1)
        grid.addWidget(self.deleteIndepVarBtn, 1, 1)

        self.paramListTblWdg       = ParameterInstanceTableView()
        self.paramListModel        = ParameterInstanceListModel(parent=self)
        self.paramListTblWdg.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.paramListTblWdg.setSelectionMode(QAbstractItemView.SingleSelection)
        self.paramListTblWdg.setModel(self.paramListModel)

        self.functionTxt        = QLineEdit(self)
        self.functionDepPartTxt    = QLabel(self)

        self.eqElementsTabs = QTabWidget(self)
        self.eqElementsTabs.addTab(self.varTab,   "Equation variables")
        self.eqElementsTabs.addTab(self.paramListTblWdg, "Equation parameters")
        #self.eqElementsTabs.setTabEnabled(1, False)
        
        #TODO: We need to implement some kind of search to allow the user to select an existing parameter.
        # It need not be from the same annotation, nor even the same paper (in case they took a parameter 
        # values from a paper they cite).

        # Signals
        self.addIndepVarBtn.clicked.connect(self.varListModel.addVariable)
        self.deleteIndepVarBtn.clicked.connect(self.varListTblWdg.deleteVariable)
        self.varListTblWdg.depTypeSelected.connect(self.setDepText)

        # Layout
        grid     = QGridLayout(self)

        grid.addWidget(self.eqElementsTabs, 0, 0, 1, 3)
        grid.addWidget(QLabel("Equation:  "), 2, 0)
        grid.addWidget(self.functionDepPartTxt, 2, 1)
        grid.addWidget(self.functionTxt, 2, 2)

    @pyqtSlot(str)
    def setDepText(self, depVar):
        self.functionDepPartTxt.setText(depVar + " = ")
        self.paramTypeSelected.emit(depVar)

    def newParameter(self):
        self.varListModel.clear()
        self.paramListModel.clear()
        self.functionTxt.setText("")
        self.functionDepPartTxt.setText("")
        self.fillingEquationParameterList()


    def saveParameter(self, relationship, paramId):
        depVar        = self.varListModel.getDepVar(varType="Variable")
        indepVars     = self.varListModel.getIndepVars(varType="Variable")

        parameters = []
        for noRow in range(self.paramListModel.rowCount()):
            paramInstanceId = self.paramListModel.getParamInstanceID(noRow)
            if self.paramListModel.selected[paramInstanceId]:
                parameters.append(ParamRef(paramInstanceId, 
                                       self.paramListModel.getParamTypeID(noRow)))

        equation        = self.functionDepPartTxt.text() + self.functionTxt.text()

        try:
            description = ParamDescFunction(depVar, indepVars, parameters, equation)
        except InvalidEquation:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Invalid equation")
            msgBox.setText("The equation '" + equation + "' is not a valid Python expression. Please correct this expression and try saving again.")
            msgBox.exec_()
            return None

        return ParameterInstance(paramId, description, [], [], relationship)


    def loadRow(self, currentParameter = None):
        #self.varListModel.load(currentParameter)
        
        if currentParameter is None:
            self.functionDepPartTxt.setText("")
            self.functionTxt.setText("")
            self.varListModel.clear()
            self.paramListModel.load([], [])        
            self.varListModel.refresh()
            self.paramListModel.refresh()
            return
            

        #paramInstances = []
        #for id in currentParameter.description.parameterIds:
        #    for param in self.mainWgt.paramListModel.parameterList:
        #        if param.id == id :
        #            paramInstances.append(param)
        #            break
        #
        #self.paramListModel.load(paramInstances)
        left, right = currentParameter.description.equation.split("=")
        left  = left.strip()
        right = right.strip()
        self.functionDepPartTxt.setText(left + " = ")
        self.functionTxt.setText(right)

        self.varListModel.setFromParam(currentParameter)
        self.varListModel.refresh()

        self.fillingEquationParameterList()





    def fillingEquationParameterList(self, currentParameter = None):
        parameters = getParametersForPub(self._parent.dbPath, Id2FileName(self._parent.currentAnnotation.pubId))
        parameters = [param for param in parameters if param.isExperimentProperty == False]
        if currentParameter is None:
            selectedParams = []
        else:
            selectedParams = [ref.instanceId for ref in currentParameter.description.parameterRefs]        
        self.paramListModel.load(parameters, selectedParams)
        self.paramListModel.refresh()
        


    def loadModelingParameter(self, row = None):
        pass


class ParameterInstanceTableView(QTableView):

    tableCheckBoxClicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegateForColumn(0, CheckBoxDelegate(self))      

    @pyqtSlot(bool)
    def checkBoxClicked(self, checked):
        # This slot will be called when our button is clicked. 
        # self.sender() returns a refence to the QPushButton created
        # by the delegate, not the delegate itself.
        #self.model().deleteRow(self.sender().row)
        self.model().selectParameter(self.sender().row, not checked)
        self.tableCheckBoxClicked.emit(self.sender().row)


class ParameterInstanceListModel(QAbstractTableModel):

    def __init__(self, colHeader = ['', 'Type', 'Description'], parent=None): #'Type',
        super().__init__(parent)
        #self.parameterList = parameterList
        self.colHeader = colHeader
        self.nbCol     = len(colHeader)
        #self.types       = []
        self.instances = []
        self.selected  = {}

    def clear(self):
        for id in self.selected:
            self.selected[id] = False
        self.refresh()

    def rowCount(self, parent=QModelIndex()):
        return len(self.instances)

    def columnCount(self, parent=QModelIndex()):
        return self.nbCol 


    def getParamInstanceID(self, row):
        return self.instances[row].id
 
    def getParamTypeID(self, row):
        return self.instances[row].description.depVar.typeId

    def getByIndex(self, param, ind):
        if ind == 0:
            return self.selected[param.id]
        elif ind == 1:
            return param.typeDesc
        elif ind == 2:
            if param.typeDesc == "pointValue":
                return param.name + " = " + param.description.depVar.values.text(True)
            elif param.typeDesc == "function":
                return param.description.equation
            elif param.typeDesc == "numericalTrace":
                return getParameterTypeNameFromID(param.description.depVar.typeId) \
                          + "=f(" + " ,".join([getParameterTypeNameFromID(v.typeId) for v in param.description.indepVars]) +  ")"
            else:
                raise ValueError
        else:
            raise ValueError


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        return self.getByIndex(self.instances[index.row()], index.column())


    def flags(self, index):
        return Qt.ItemIsEditable | Qt.ItemIsEnabled



    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.colHeader[section]        
        return None


    def load(self, paramInstances, selectedIDs):
        self.instances = paramInstances
        self.selected  = {}
        for row, instance in enumerate(self.instances):
            ID = self.getParamInstanceID(row)
            self.selected[ID] = ID in selectedIDs
        self.refresh()
        
    def selectParameter(self, row, selected):
        ID = self.getParamInstanceID(row)
        self.selected[ID] = selected     


    def refresh(self):
        self.layoutChanged.emit()
