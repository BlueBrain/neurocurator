#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtCore import Qt, QAbstractTableModel
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QModelIndex
from PyQt5.QtWidgets import QMessageBox, QTableView

from nat.modelingParameter import (getParameterTypes, getParameterTypeIDFromName,
                                   getParameterTypeFromID, ParameterTypeTree)
from nat.paramDesc import ParamDescFunction, ParamDescTrace
from nat.values import ValuesSimple, ValuesCompound
from nat.variable import Variable, NumericalVariable
from .itemDelegates import (DoubleDelegate, ParamTypeDelegate, UnitDelegate,
                            StatisticsDelegate)


parameterTypeTree = ParameterTypeTree.load()
parameterTypes = getParameterTypes()


class VariableTableView(QTableView):

    depTypeSelected  = pyqtSignal(str)
    #selectionChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(DoubleDelegate(self))
        typeDelegate = ParamTypeDelegate(self)
        self.setItemDelegateForRow(0, typeDelegate)
        self.setItemDelegateForRow(1, UnitDelegate(self))
        self.setItemDelegateForRow(2, StatisticsDelegate(self))
        typeDelegate.typeSelected.connect(self.typeSelected)

    @pyqtSlot(str)
    def typeSelected(self, paramType):
        if self.selectionModel().currentIndex().column() == 0:
            self.depTypeSelected.emit(paramType)

    def deleteVariable(self):
        self.model().deleteVariable(self.selectionModel().currentIndex().column())

    def deleteSample(self):
        self.model().deleteSample(self.selectionModel().currentIndex().row())


class VariableListModel(QAbstractTableModel):

    def __init__(self, colHeader = ['Dependant', 'Independant 1'], rowHeader = ['Type', 'Unit', 'Statistic'], parent=None):
        super().__init__(parent)
        self.clear(colHeader, rowHeader)

    def clear(self, colHeader = ['Dependant', 'Independant 1'], rowHeader = ['Type', 'Unit', 'Statistic']):
        self.colHeader = colHeader
        self.rowHeader = rowHeader
        self.nbSample  = 0
        self.nbDep     = 1
        self.nbIndep   = 1
        self.__data       = {} 
        for col in colHeader:        
            for row in rowHeader:
                if row == "Statistic":
                    self.__data[(row, col)] = "raw"
                elif row == "Unit":
                    self.__data[(row, col)] = "dimensionless"        
                else:
                    self.__data[(row, col)] = None
        self.refresh()



    def setFromParam(self, param):
        if isinstance(param.description, ParamDescFunction):
            self.__data = {}
            self.__data[('Type',       'Dependant')] = getParameterTypeFromID(param.description.depVar.typeId).name
            self.__data[('Unit',       'Dependant')] = param.description.depVar.unit
            self.__data[('Statistic',  'Dependant')] = param.description.depVar.statistic
            self.colHeader = ['Dependant']

            for colInd in range(1, len(param.description.indepVars)+1):
                colName = 'Independant ' + str(colInd)        
                self.colHeader.append(colName)
                self.__data[('Type',       colName)] = getParameterTypeFromID(param.description.indepVars[colInd-1].typeId).name
                self.__data[('Unit',       colName)] = param.description.indepVars[colInd-1].unit
                self.__data[('Statistic', colName)] = param.description.indepVars[colInd-1].statistic

        elif isinstance(param.description, ParamDescTrace):
            self.__data = {}      
            valuesObject = param.description.depVar.values
            self.__data[('Type', 'Dependant')] = getParameterTypeFromID(param.description.depVar.typeId).name    
            
            #### Add the appropriate number of samples
            self.nbSample = 0
            self.rowHeader = self.rowHeader[:3]
            for noSample in range(len(param.description.indepVars[0].values.values)):
                self.addSample(refresh=False)            
            
            self.colHeader = ['Dependant']
            
            #### ValuesCompound as dependant variable
            if isinstance(valuesObject, ValuesCompound):
                self.nbDep = len(valuesObject.valueLst)
                for ind, val in enumerate(valuesObject.valueLst):
                    if ind == 0:                       
                        varName = "Dependant"                    
                    else:
                        varName = "Dependant comp. " + str(ind+1)   
                        self.colHeader.append(varName)
                        self.__data[('Type', varName)] = self.__data[('Type', 'Dependant')]  
                        
                    self.__data[('Unit',       varName)] = val.unit
                    self.__data[('Statistic',  varName)] = val.statistic

                    for noSample, sample in enumerate(val.values):
                        self.__data[(str(noSample+1), varName)] = sample

            #### ValuesSimple as dependant variable  
            elif isinstance(valuesObject, ValuesSimple):

                self.__data[('Unit',       'Dependant')] = valuesObject.unit
                self.__data[('Statistic',  'Dependant')] = valuesObject.statistic
    
                self.nbDep = 1
                for noSample, sample in enumerate(valuesObject.values):
                    self.__data[(str(noSample+1), 'Dependant')] = sample

            #### Independant variables

            self.nbIndep = len(param.description.indepVars)
            for colInd in range(self.nbDep, self.nbIndep+self.nbDep):
                colName = 'Independant ' + str(colInd)        
                self.colHeader.append(colName)
                self.__data[('Type',       colName)] = getParameterTypeFromID(param.description.indepVars[colInd-self.nbDep].typeId).name
                self.__data[('Unit',       colName)] = param.description.indepVars[colInd-self.nbDep].values.unit
                self.__data[('Statistic', colName)] = param.description.indepVars[colInd-self.nbDep].values.statistic

                for noSample, sample in enumerate(param.description.indepVars[colInd-self.nbDep].values.values):
                    self.__data[(str(noSample+1), colName)] = sample
        else:
            raise TypeError

        self.refresh()

    def getIndepVars(self, varType="Variable"):
        if varType == "Variable":
            return [Variable(getParameterTypeIDFromName(self.__data[('Type',      varLabel)]), 
                                                        self.__data[('Unit',      varLabel)], 
                                                        self.__data[('Statistic', varLabel)])
                        for varLabel in self.colHeader if "Independant" in varLabel]

        elif varType == "NumericalVariable":
            indepVars = []
            for varLabel in self.colHeader:
                if not "Independant" in varLabel:
                    continue
                floatValues = []
                for row in self.rowHeader[3:]:
                    try:
                        floatValues.append(float(self.__data[(row, varLabel)]))
                    except ValueError:
                        floatValues.append(float('nan'))

                values = ValuesSimple(floatValues, self.__data[('Unit',      varLabel)], 
                                                    self.__data[('Statistic', varLabel)])

                typeId = getParameterTypeIDFromName(self.__data[('Type', varLabel)])
                indepVars.append(NumericalVariable(typeId, values))
            return indepVars

        else:
            raise ValueError



    def getDepVar(self, varType="Variable"):
        
        if varType == "Variable":
            typeId = getParameterTypeIDFromName(self.__data[('Type', 'Dependant')])
            return Variable(typeId, 
                            self.__data[('Unit',      'Dependant')], 
                            self.__data[('Statistic', 'Dependant')])
                            
        elif varType == "NumericalVariable":
            depVarValues = []
            
            for varLabel in self.colHeader:
                if not "Dependant" in varLabel:
                    continue            
                if varLabel == "Dependant" :
                    typeId  = getParameterTypeIDFromName(self.__data[('Type', varLabel)])
                
                floatValues = []
                for row in self.rowHeader[3:]:
                    try:
                        floatValues.append(float(self.__data[(row, varLabel)]))
                    except ValueError:
                        floatValues.append(float('nan'))
    
                values = ValuesSimple(floatValues, self.__data[('Unit',      varLabel)], 
                                                   self.__data[('Statistic', varLabel)])
    
                if self.nbDep == 1 :
                    return NumericalVariable(typeId, values)   
                else:
                    depVarValues.append(values)
            
            values = ValuesCompound(depVarValues)
            
            return NumericalVariable(typeId, values)   
                
        else:
            raise ValueError



    def rowCount(self, parent=QModelIndex()):
        return len(self.rowHeader)

    def columnCount(self, parent=QModelIndex()):
        return len(self.colHeader)


    def getType(self, col):
        return self.__data["Type", self.colHeader[col]]

    def getUnit(self, col):
        return self.__data["Unit", self.colHeader[col]]

    def getStatistic(self, col):
        return self.__data["Statistic", self.colHeader[col]]


    def addVariable(self):      
        inc = 1
        col = 'Independant ' + str(self.nbIndep+inc)
        while col in self.colHeader:
            inc += 1
            col = 'Independant ' + str(self.nbIndep+inc)
            
        self.colHeader.append(col)
        for row in self.rowHeader:
            if row == "Statistic":
                self.__data[(row, col)] = "raw"
            elif row == "Unit":
                self.__data[(row, col)] = "dimensionless"                
            else:
                self.__data[(row, col)] = None

        self.nbIndep += 1  
        self.refresh()


    def addDepCompnent(self):
        inc = 1
        col = 'Dependant comp. ' + str(self.nbDep+inc)
        while col in self.colHeader:
            inc += 1
            col = 'Dependant comp. ' + str(self.nbDep+inc)
                    
        self.colHeader.insert(self.nbDep, col)
        for row in self.rowHeader:
            if row == "Statistic":
                self.__data[(row, col)] = "raw"
            elif row == "Unit":
                self.__data[(row, col)] = "dimensionless"     
            elif row == "Type":
                self.__data[(row, col)] = self.__data[(row, 'Dependant')]                
            else:
                self.__data[(row, col)] = None

        self.nbDep += 1
        self.refresh()




    def addSample(self, refresh=True):
        self.nbSample += 1
        row = str(self.nbSample)
        self.rowHeader.append(row)
        for col in self.colHeader:
            self.__data[(row, col)] = None

        if refresh:
            self.refresh()



    def deleteVariable(self, col):

        msgBox = QMessageBox()
        msgBox.setWindowTitle("Deletion")
        msgBox.setText("Are you sure you want to delete the variable '" + self.colHeader[col] + "'?")
        msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.No)
        if msgBox.exec_() == QMessageBox.Yes:
            for rowName in self.rowHeader:
                del self.__data[(rowName, self.colHeader[col])]
                
            if "Independant" in self.colHeader[col]:
                self.nbIndep -= 1
            else:
                self.nbDep -= 1 
                
            del self.colHeader[col]
        self.refresh()
        
        

    def deleteSample(self, noRow):

        msgBox = QMessageBox()
        msgBox.setWindowTitle("Deletion")
        msgBox.setText("Are you sure you want to delete the sample at index " + self.rowHeader[noRow] + "?")
        msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
        msgBox.setDefaultButton(QMessageBox.No)
        if msgBox.exec_() == QMessageBox.Yes:
            for colName in self.colHeader:
                del self.__data[(self.rowHeader[noRow], colName)]
            del self.rowHeader[noRow]

        self.refresh()


    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole and  role != Qt.EditRole:
            return None

        return str(self.__data[(self.rowHeader[index.row()], self.colHeader[index.column()])])



    def setData(self, index, value, role=Qt.DisplayRole):
        if value is None:
            value = ""
            
        if self.colHeader[index.column()] == "Dependant" and self.rowHeader[index.row()] == "Type":
            for colName in self.rowHeader:
                if 'Dependant comp. ' in colName:
                    self.__data[(self.rowHeader[index.row()], colName)] = value
                        
        self.__data[(self.rowHeader[index.row()], self.colHeader[index.column()])] = value
        return True


    def flags(self, index):
        if "comp." in self.colHeader[index.column()] and self.rowHeader[index.row()] == "Type":
            return Qt.NoItemFlags
            
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled


    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.colHeader[section]        
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return self.rowHeader[section]
        return None


    def refresh(self):
        self.layoutChanged.emit()

    def load(self, param):
        #param.description.
        ### TODO: LOAD FROM PARAM
        self.refresh()

