#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore


from nat.modelingParameter import getParameterTypes, getParameterTypeIDFromName, \
    getParameterTypeFromID, ParameterTypeTree, Variable, ParamDescFunction, \
     ValuesSimple, NumericalVariable, ParamDescTrace

from .itemDelegates import DoubleDelegate, ParamTypeDelegate, UnitDelegate, StatisticsDelegate

parameterTypeTree     = ParameterTypeTree.load()
parameterTypes         = getParameterTypes()


class VariableTableView(QtGui.QTableView):

    depTypeSelected = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super(VariableTableView, self).__init__(*args, **kwargs)

        self.setItemDelegate(DoubleDelegate(self))
        typeDelegate = ParamTypeDelegate(self)
        self.setItemDelegateForRow(0, typeDelegate)
        self.setItemDelegateForRow(1, UnitDelegate(self))
        self.setItemDelegateForRow(2, StatisticsDelegate(self))

        typeDelegate.typeSelected.connect(self.typeSelected)


    @QtCore.Slot(object, str)
    def typeSelected(self, paramType):
        if self.selectionModel().currentIndex().column() == 0:
            self.depTypeSelected.emit(paramType)

    def deleteVariable(self):
        self.model().deleteVariable(self.selectionModel().currentIndex().column())

    def deleteSample(self):
        self.model().deleteSample(self.selectionModel().currentIndex().row())




class VariableListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, colHeader = ['Dependant', 'Independant 1'], rowHeader = ['Type', 'Unit', 'Statistic'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        #self.parameterList = parameterList
        self.clear(colHeader, rowHeader)

    def clear(self, colHeader = ['Dependant', 'Independant 1'], rowHeader = ['Type', 'Unit', 'Statistic']):
        self.colHeader = colHeader
        self.rowHeader = rowHeader
        self.nbSample  = 0
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
            self.__data[('Statistic', 'Dependant')] = param.description.depVar.statistic
            self.colHeader = ['Dependant']

            for colInd in range(1, len(param.description.indepVars)+1):
                colName = 'Independant ' + str(colInd)        
                self.colHeader.append(colName)
                self.__data[('Type',       colName)] = getParameterTypeFromID(param.description.indepVars[colInd-1].typeId).name
                self.__data[('Unit',       colName)] = param.description.indepVars[colInd-1].unit
                self.__data[('Statistic', colName)] = param.description.indepVars[colInd-1].statistic

        elif isinstance(param.description, ParamDescTrace):
            self.__data = {}
            self.__data[('Type',       'Dependant')] = getParameterTypeFromID(param.description.depVar.typeId).name
            self.__data[('Unit',       'Dependant')] = param.description.depVar.values.unit
            self.__data[('Statistic', 'Dependant')] = param.description.depVar.values.statistic
            self.colHeader = ['Dependant']

            self.nbSample = 0
            self.rowHeader = self.rowHeader[:3]
            for noSample in range(len(param.description.indepVars[0].values.values)):
                self.addSample(refresh=False)



            for noSample, sample in enumerate(param.description.depVar.values.values):
                self.__data[(str(noSample+1), 'Dependant')] = sample

            for colInd in range(1, len(param.description.indepVars)+1):
                colName = 'Independant ' + str(colInd)        
                self.colHeader.append(colName)
                self.__data[('Type',       colName)] = getParameterTypeFromID(param.description.indepVars[colInd-1].typeId).name
                self.__data[('Unit',       colName)] = param.description.indepVars[colInd-1].values.unit
                self.__data[('Statistic', colName)] = param.description.indepVars[colInd-1].values.statistic

                for noSample, sample in enumerate(param.description.indepVars[colInd-1].values.values):
                    self.__data[(str(noSample+1), colName)] = sample
        else:
            raise TypeError



    def getIndepVars(self, varType="Variable"):
        if varType == "Variable":
            return [Variable(getParameterTypeIDFromName(self.__data[('Type',      'Independant ' + str(no))]), 
                             self.__data[('Unit',      'Independant ' + str(no))], 
                             self.__data[('Statistic', 'Independant ' + str(no))])
                        for no in range(1, self.columnCount())]

        elif varType == "NumericalVariable":
            indepVars = []
            for no in range(1, self.columnCount()):
                varLabel    = 'Independant ' + str(no)
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
            floatValues = []
            for row in self.rowHeader[3:]:
                try:
                    floatValues.append(float(self.__data[(row,'Dependant')]))
                except ValueError:
                    floatValues.append(float('nan'))

            values = ValuesSimple(floatValues, self.__data[('Unit',      'Dependant')], 
                                                self.__data[('Statistic', 'Dependant')])

            typeId = getParameterTypeIDFromName(self.__data[('Type', 'Dependant')])
            return NumericalVariable(typeId, values)

        else:
            raise ValueError





    """

        if varType == "Variable":
            return [Variable(getParameterTypeIDFromName(self.__data[('Type',      'Independant ' + str(no))]), 
                             self.__data[('Unit',      'Independant ' + str(no))], 
                             self.__data[('Statistic', 'Independant ' + str(no))])
                        for no in range(1, self.columnCount())]

        elif varType == "NumericalVariable":
            indepVars = []

            # Generally, one ValuesSimple object is created by independant variable.
            # However, when two independant variables are asstributed to a same 
            # parameter, this is interpreted as different statistics that 
            # should be combined in a given ValuesCompound object.
            typeDic = {}
            for no in range(1, self.columnCount()):
                varLabel    = 'Independant ' + str(no)   
                itemType    = self.__data[('Type', varLabel)]
                if itemType in typeDic:                    
                    typeDic[itemType].append((no, varLabel))
                else:
                    typeDic[itemType] = [(no, varLabel)]
            
            ## loop dic items, create ValuesSimple for list of 1 element, 
            ## create ValuesCompound for lists of more than one element...            
            for itemType, noLst in typeDic.items():
                varLst = []
                for no, varLabel in noLst:
                    
                    floatValues = []
                    for row in self.rowHeader[3:]:
                        try:
                            floatValues.append(float(self.__data[(row, varLabel)]))
                        except ValueError:
                            floatValues.append(float('nan'))
    
                    varLst.append(ValuesSimple(floatValues, self.__data[('Unit',      varLabel)], 
                                                        self.__data[('Statistic', varLabel)]))
    
                typeId = getParameterTypeIDFromName(self.__data[('Type', varLabel)])
                if len(varLst) == 1:
                    indepVars.append(NumericalVariable(typeId, varLst[0]))
                else:
                    indepVars.append(NumericalVariable(typeId, ValuesCompound(varLst)))
            
            return indepVars

        else:
            raise ValueError    
    
    """








    def rowCount(self, parent=None):
        return len(self.rowHeader)

    def columnCount(self, parent=None):
        return len(self.colHeader)


    def getType(self, col):
        return self.__data["Type", self.colHeader[col]]

    def getUnit(self, col):
        return self.__data["Unit", self.colHeader[col]]

    def getStatistic(self, col):
        return self.__data["Statistic", self.colHeader[col]]


    def addVariable(self):
        col = 'Independant ' + str(self.columnCount())
        self.colHeader.append(col)
        for row in self.rowHeader:
            if row == "Statistic":
                self.__data[(row, col)] = "raw"
            elif row == "Unit":
                self.__data[(row, col)] = "dimensionless"                
            else:
                self.__data[(row, col)] = None

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

        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle("Deletion")
        msgBox.setText("Are you sure you want to delete the variable '" + self.colHeader[col] + "'?")
        msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
        msgBox.setDefaultButton(QtGui.QMessageBox.No)
        if msgBox.exec_() == QtGui.QMessageBox.Yes:
            for rowName in self.rowHeader:
                del self.__data[(rowName, self.colHeader[col])]
            del self.colHeader[col]
        self.refresh()



    def deleteSample(self, noRow):

        msgBox = QtGui.QMessageBox()
        msgBox.setWindowTitle("Deletion")
        msgBox.setText("Are you sure you want to delete the sample at index " + self.rowHeader[noRow] + "?")
        msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
        msgBox.setDefaultButton(QtGui.QMessageBox.No)
        if msgBox.exec_() == QtGui.QMessageBox.Yes:
            for colName in self.colHeader:
                del self.__data[(self.rowHeader[noRow], colName)]
            del self.rowHeader[noRow]

        #for noRow in range(3, len(self.rowHeader)):
        #    self.rowHeader[noRow] = str(noRow -2)

        self.refresh()


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole and  role != QtCore.Qt.EditRole:
            return None

        return self.__data[(self.rowHeader[index.row()], self.colHeader[index.column()])]



    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if value is None:
            value = ""
        self.__data[(self.rowHeader[index.row()], self.colHeader[index.column()])] = value
        return True

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled


    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.colHeader[section]        
        elif orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return self.rowHeader[section]
        return None


    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def load(self, param):
        #param.description.
        ### TODO: LOAD FROM PARAM
        self.refresh()

