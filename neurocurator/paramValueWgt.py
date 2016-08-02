#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore


from nat.modelingParameter import getParameterTypes, ParameterInstance, \
    getParameterTypeIDFromName, ValuesSimple, ValuesCompound, ParamDescPoint, \
    NumericalVariable

from .itemDelegates import ParamTypeCbo, DoubleDelegate, UnitDelegate, \
    StatisticsDelegate, ButtonDelegate


parameterTypes         = getParameterTypes()


class ParamValueWgt(QtGui.QWidget):

    paramTypeSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ParamValueWgt, self).__init__()

        self.parent = parent

        # Widgets        
        self.paramsEdit       = ParamTypeCbo(self)
        self.paramDescription = QtGui.QTextEdit(self)
        self.valListTblWdg    = ValueTableView() 
        self.valListModel     = ValueListModel(self)
        self.valListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.valListTblWdg.setModel(self.valListModel)


        # Signals
        self.paramsEdit.activated[str].connect(self.paramTypeChanged)


        # Layout
        grid     = QtGui.QGridLayout(self)
        grid.addWidget(QtGui.QLabel("Parameter"), 0, 0)
        grid.addWidget(self.paramsEdit,           0, 1)
        grid.addWidget(self.paramDescription, 1, 0, 1, 2)
        grid.addWidget(self.valListTblWdg, 2, 0, 1, 2)


        # Initial behavior
        self.paramDescription.setReadOnly(True)



    @property
    def selectedTags(self):
        return self.parent.getSelectedTags()


    def paramTypeChanged(self, paramName):
        self.paramTypeSelected.emit(paramName)
        for paramType in parameterTypes:
            if paramType.name == paramName:
                self.paramDescription.setText(paramType.description)
            

    def newParameter(self):
        self.additionMode = True

        self.valListModel.clear()
        self.paramsEdit.setCurrentIndex(-1)
        self.paramDescription.setText("")
        self.paramsEdit.setFocus()


    def saveParameter(self, relationship, paramId):

        error = None
        typeID = getParameterTypeIDFromName(self.paramsEdit.currentText())
        if typeID is None:
            error = "parameter type"
        
        if error is None:
            values = NumericalVariable(typeID, self.valListModel.getValuesObject())
            description    = ParamDescPoint(values)
            return ParameterInstance(paramId, description, [], relationship)

        else:
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Invalid modeling parameter")
            msgBox.setText("To save this annotation with an associated modeling parameter, a valid value and unit must be entered. The " + error + " entered is not valid.")
            msgBox.exec_() 
            return None

        
    def loadRow(self, currentParameter):
        if currentParameter is None:
            self.valListModel.clear()
            self.paramsEdit.setCurrentIndex(-1)
            self.paramDescription.setText("")
        else:
            self.valListModel.setFromParameter(currentParameter)    
            for i in range(self.paramsEdit.count()):
                if self.paramsEdit.itemText(i) == currentParameter.name:
                    self.paramsEdit.setCurrentIndex(i)
                    self.paramTypeChanged(currentParameter.name)
                    break


    def loadModelingParameter(self, row = None):
        if row is None:
            self.loadRow(None)
        else:
            self.loadRow(self.parent.currentAnnotation.parameters[row])







class ValueTableView(QtGui.QTableView):

    def __init__(self, *args, **kwargs):
        QtGui.QTableView.__init__(self, *args, **kwargs)
        
        self.setItemDelegateForColumn(0, DoubleDelegate(self))
        self.setItemDelegateForColumn(1, UnitDelegate(self))
        self.setItemDelegateForColumn(2, StatisticsDelegate(self))
        self.setItemDelegateForColumn(3, ButtonDelegate(self))



    @QtCore.Slot(object) #, str
    def cellButtonClicked(self):
        # This slot will be called when our button is clicked. 
        # self.sender() returns a refence to the QPushButton created
        # by the delegate, not the delegate itself.
        self.model().deleteRow(self.sender().row)


class ValueListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, colHeader = ['Values', 'Unit', 'Statistic', 'delete'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        #self.parameterList = parameterList
        self.clear(colHeader)

    def clear(self, colHeader = ['Values', 'Unit', 'Statistic', 'delete']):
        self.colHeader = colHeader
        self.values    = [] 

        self.refresh()



    def rowCount(self, parent=None):
        return len(self.values)+1

    def columnCount(self, parent=None):
        return len(self.colHeader)


    def getValues(self, row):
        return self.values[row].values

    def getUnit(self, row):
        return self.values[row].unit

    def getStatistic(self, row):
        return self.values[row].statistic

    
    def getDataByIndex(self, row, col):
        if row == self.rowCount()-1:
            return ""
        
        if col == 0:
            values = self.getValues(row)
            if len(values) == 1:
                return str(values[0])
            else:
                return str(values)
        elif col == 1:
            return self.getUnit(row)
        elif col == 2 :
            return self.getStatistic(row)
        else:
            return None


    def setDataByIndex(self, row, col, data):
        if row == self.rowCount()-1:
            self.values.append(ValuesSimple())
            self.refresh()
        
        if col == 0:
            values = eval(data)
            if isinstance(values, list):
                self.values[row].values    = values
            else:
                self.values[row].values    = [values]
                
        elif col == 1:
            self.values[row].unit      = data
        elif col == 2 :
            self.values[row].statistic = data
        else:
            return False
        return True


    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole and  role != QtCore.Qt.EditRole:
            return None

        return self.getDataByIndex(index.row(), index.column())



    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if value is None:
            value = ""
        return self.setDataByIndex(index.row(), index.column(), value)
        


    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled



    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.colHeader[section]        
        return None


    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def getValuesObject(self):
        """
         Return a ValuesSimple object if only one row has been filed, else
         return a ValuesCompounded object containing all rows.
        """

        if self.rowCount() == 2:
            # Only one row is filed. An empty row is always appended to filed rows.
            return self.values[0]
        else:
            return ValuesCompounded(self.values)
            
            
    def deleteRow(self, row):
        if row >= 0 and row < len(self.values):
            del self.values[row]
            self.refresh()

            
    def setFromParameter(self, parameter):
        if parameter is None:
            self.values = []
        elif isinstance(parameter.description.depVar, NumericalVariable):
            valuesObject = parameter.description.depVar.values
            if isinstance(valuesObject, ValuesSimple):
                self.values = [valuesObject]
            elif isinstance(valuesObject, ValuesCompounded):
                self.values = valuesObject.valueLst
            else:
                raise TypeError
        else:
            raise TypeError

        self.refresh()
        
        
        