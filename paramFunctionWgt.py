#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore

from modelingParameter import getParameterTypes, ParameterInstance, \
    ParameterTypeTree, ParamDescFunction, InvalidEquation, \
    getParameterTypeNameFromID, ParamRef
from itemDelegates import CheckBoxDelegate
from utils import getParametersForPub
from variableTableWgt import VariableTableView, VariableListModel
from utils import Id2FileName

parameterTypeTree     = ParameterTypeTree.load()
parameterTypes        = getParameterTypes()



class ParamFunctionWgt(QtGui.QWidget):

    paramTypeSelected = QtCore.Signal(str)
    
    def __init__(self, parent):
        super(ParamFunctionWgt, self).__init__()
        self.parent = parent
        self.parameterTypes = getParameterTypes()

        # Widgets        
        self.addIndepVarBtn        = QtGui.QPushButton("Add variable")
        self.deleteIndepVarBtn     = QtGui.QPushButton("Delete variable")
        self.varListTblWdg         = VariableTableView() 
        self.varListModel          = VariableListModel(self)
        self.varListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.varListTblWdg.setModel(self.varListModel)

        self.varTab                = QtGui.QWidget(self)    
        grid                       = QtGui.QGridLayout(self.varTab)
        grid.addWidget(self.varListTblWdg, 0, 0, 3, 1)
        grid.addWidget(self.addIndepVarBtn, 0, 1)
        grid.addWidget(self.deleteIndepVarBtn, 1, 1)

        self.paramListTblWdg       = ParameterInstanceTableView()
        self.paramListModel        = ParameterInstanceListModel(self)
        self.paramListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.paramListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.paramListTblWdg.setModel(self.paramListModel)

        self.functionTxt        = QtGui.QLineEdit(self)
        self.functionDepPartTxt    = QtGui.QLabel(self)

        self.eqElementsTabs = QtGui.QTabWidget(self)
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
        grid     = QtGui.QGridLayout(self)

        grid.addWidget(self.eqElementsTabs, 0, 0, 1, 3)
        grid.addWidget(QtGui.QLabel("Equation:  "), 2, 0)
        grid.addWidget(self.functionDepPartTxt, 2, 1)
        grid.addWidget(self.functionTxt, 2, 2)



    @QtCore.Slot(object, str)
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
            msgBox = QtGui.QMessageBox(self)
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
        parameters = getParametersForPub(self.parent.dbPath, Id2FileName(self.parent.currentAnnotation.pubId))
        parameters = [param for param in parameters if param.isExperimentProperty == False]
        if currentParameter is None:
            selectedParams = []
        else:
            selectedParams = [ref.instanceId for ref in currentParameter.description.parameterRefs]        
        self.paramListModel.load(parameters, selectedParams)
        self.paramListModel.refresh()
        


    def loadModelingParameter(self, row = None):
        pass












class ParameterInstanceTableView(QtGui.QTableView):


    tableCheckBoxClicked = QtCore.Signal(int)

    def __init__(self, *args, **kwargs):
        QtGui.QTableView.__init__(self, *args, **kwargs)
        
        self.setItemDelegateForColumn(0, CheckBoxDelegate(self))      

    @QtCore.Slot(object) #, str
    def checkBoxClicked(self):
        # This slot will be called when our button is clicked. 
        # self.sender() returns a refence to the QPushButton created
        # by the delegate, not the delegate itself.
        #self.model().deleteRow(self.sender().row)
        self.model().selectParameter(self.sender().row, not self.sender().isChecked())
        self.tableCheckBoxClicked.emit(self.sender().row)


class ParameterInstanceListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, colHeader = ['', 'Type', 'Description'], *args): #'Type', 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
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

    def rowCount(self, parent=None):
        return len(self.instances)

    def columnCount(self, parent=None):
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


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        return self.getByIndex(self.instances[index.row()], index.column())


    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled



    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
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
        self.emit(QtCore.SIGNAL("layoutChanged()"))

