#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui, QtCore

from nat.modelingParameter import getParameterTypeFromName, \
    getParameterTypeNameFromID
from nat.ontoManager import OntoManager  
from nat.tag import RequiredTag

from .itemDelegates import ReqTagDelegate
from .paramFunctionWgt import ParamFunctionWgt
from .paramRelationWgt import ParamRelationWgt
from .paramTraceWgt import ParamTraceWgt
from .paramValueWgt import ParamValueWgt 



class RequiredTagsTableView(QtGui.QTableView):

    setReqTags = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        QtGui.QTableView.__init__(self, *args, **kwargs)
        self.reqTagDelegate = ReqTagDelegate(self)
        self.setItemDelegateForColumn(1, self.reqTagDelegate)
        ontoMng = OntoManager()
        self.treeData                  = ontoMng.trees 
        self.dicData                   = ontoMng.dics
        self.reqTagDelegate.cboNeedPopulation.connect(self.setReqTags)

    def setReqTags(self, tagName):

        tagId = list(self.dicData.keys())[list(self.dicData.values()).index(tagName)]
        
        if not tagId in self.treeData:
            raise ValueError("The term id " + tagId + " was not specified as an ontological root.")

        self.reqTagDelegate.addItems(list(self.treeData[tagId].values()))




class RequiredTagsListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, colHeader = ['Required categorie', 'Selected tag'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)

        self.colHeader             = colHeader
        self.nbCol                 = len(colHeader)
        self.requiredTagsIds       = []
        self.requiredTagsNames     = []
        self.selectedTagsIds       = []
        self.selectedTagsNames     = []
        ontoMng = OntoManager()
        self.treeData                  = ontoMng.trees 
        self.dicData                   = ontoMng.dics


    def rowCount(self, parent=None):
        return len(self.requiredTagsNames)

    def columnCount(self, parent=None):
        return self.nbCol 

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        if index.column() == 0:
            return self.requiredTagsNames[index.row()]
        elif index.column() == 1:
            return self.selectedTagsNames[index.row()]
        else:
            return None

    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        if value is None:
            value = ""

        if index.column() == 0:
            self.requiredTagsNames[index.row()] = value
            tagId = list(self.dicData.keys())[list(self.dicData.values()).index(value)]            
            self.requiredTagsIds[index.row()]   = tagId
            
        elif index.column() == 1:
            if self.checkTagValidity(index.row(), value):
                self.selectedTagsNames[index.row()] = value
                tagId = list(self.dicData.keys())[list(self.dicData.values()).index(value)]    
                self.selectedTagsIds[index.row()]   = tagId

    def checkTagValidity(self, row, tagName):

        tagId = self.requiredTagsIds[row]

        if not tagId in self.treeData: 

            #print(self.requiredTagsIds[row], self.requiredTagsNames[row], self.selectedTagsIds[row], self.selectedTagsNames[row]) 
            #print(self.treeData[self.requiredTagsIds[row]])     
            raise ValueError("Tag '" + tagId + "' is not a treeData root. TreeData roots are the following:" + str(list(self.treeData.keys())))

        return tagName in list(self.treeData[tagId].values())


    def flags(self, index):
        if index.column() == 0:
            result = super(RequiredTagsListModel, self).flags(index)
            result &= ~QtCore.Qt.ItemIsEditable
            return result
        else:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.colHeader[section]        
        return None

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def addTag(self, requiredTagId, requiredTagName, selectedTagId, selectedTagName):
        self.requiredTagsNames.append(requiredTagName)
        self.requiredTagsIds.append(requiredTagId)
        self.selectedTagsNames.append(selectedTagName)
        self.selectedTagsIds.append(selectedTagId)
        self.refresh()
        print(requiredTagId, requiredTagName, selectedTagId, selectedTagName)

    def clear(self):
        self.requiredTagsNames  = []
        self.requiredTagsIds    = []
        self.selectedTagsNames  = []
        self.selectedTagsIds    = []
        self.refresh()

    def getRequiredTags(self):
        return [RequiredTag(id, name, rootId) for id, name, rootId in zip(self.selectedTagsIds, self.selectedTagsNames, self.requiredTagsIds)]





class ParamModWgt(QtGui.QWidget):

    def __init__(self, parent):

        self.parent = parent
        super(ParamModWgt, self).__init__()

        self.buildRequiredTagsGB()

        # Widgets        
        self.newParamBtn        = QtGui.QPushButton("New")
        self.deleteParamBtn     = QtGui.QPushButton("Delete")
        self.paramSaveAnnotBtn  = QtGui.QPushButton("Save") 
        buttonWidget             = QtGui.QWidget(self)

        self.existingParamsGB     = QtGui.QGroupBox("Existing parameters", self)

        self.paramListTblWdg      = QtGui.QTableView() 
        self.paramListModel     = ParameterListModel(self)
        self.paramListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.paramListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.paramListTblWdg.setModel(self.paramListModel)

        self.paramListTblWdg.setColumnWidth(0, 150)
        self.paramListTblWdg.setColumnWidth(1, 350)

        self.relationWgt    = ParamRelationWgt(parent)
        self.newParamsGB    = QtGui.QGroupBox("Parameter details", self)
        self.resultTypeCbo  = QtGui.QComboBox(self)
        self.isExpProp      = QtGui.QCheckBox("is an experimental property", self)

        self.resultTypeCbo.addItems(["point value", "function", "numerical trace"])
        
        self.singleValueParamWgt = ParamValueWgt(parent)
        self.functionParamWgt    = ParamFunctionWgt(parent)
        self.traceParamWgt       = ParamTraceWgt(parent)

        self.functionParamWgt.mainWgt = self

        self.paramModStack       = QtGui.QStackedWidget(self)
        self.paramModStack.addWidget(self.singleValueParamWgt)
        self.paramModStack.addWidget(self.functionParamWgt)
        self.paramModStack.addWidget(self.traceParamWgt)


        # Signals
        selectionModel = self.paramListTblWdg.selectionModel()
        selectionModel.selectionChanged.connect(self.selectedParameterChanged)

        self.newParamBtn.clicked.connect(self.newParameter)
        self.deleteParamBtn.clicked.connect(self.deleteParameter)
        self.paramSaveAnnotBtn.clicked.connect(self.saveParameter)
        self.resultTypeCbo.currentIndexChanged.connect(self.paramModStack.setCurrentIndex)
        self.singleValueParamWgt.paramTypeSelected.connect(self.newParamTypeSelected)
        self.functionParamWgt.paramTypeSelected.connect(self.newParamTypeSelected)
        self.traceParamWgt.paramTypeSelected.connect(self.newParamTypeSelected)


        # Layout
        buttonLayout = QtGui.QVBoxLayout(buttonWidget)
        buttonLayout.addWidget(self.paramSaveAnnotBtn)
        buttonLayout.addWidget(self.deleteParamBtn)
        buttonLayout.addWidget(self.newParamBtn)

        existGrid     = QtGui.QHBoxLayout(self.existingParamsGB)
        existGrid.addWidget(buttonWidget)
        existGrid.addWidget(self.paramListTblWdg)
        
        newGrid     = QtGui.QGridLayout(self.newParamsGB)
        newGrid.addWidget(QtGui.QLabel("Result type"), 0, 0)
        newGrid.addWidget(self.resultTypeCbo, 0, 1)
        newGrid.addWidget(self.isExpProp, 0, 2)
        
        newGrid.addWidget(self.paramModStack, 1, 0, 1, 3)
        newGrid.addWidget(self.relationWgt, 1, 3)

        layout = QtGui.QVBoxLayout(self)        
        self.rootLayout = QtGui.QSplitter(QtCore.Qt.Vertical, parent=self)
        self.rootLayout.setOrientation(QtCore.Qt.Vertical)
        self.rootLayout.addWidget(self.existingParamsGB)
        self.rootLayout.addWidget(self.newParamsGB)
        self.rootLayout.addWidget(self.requireTagGB)
        layout.addWidget(self.rootLayout)

        # Initial behavior
        self.newParamBtn.setEnabled(True)
        self.deleteParamBtn.setEnabled(False)
        self.paramSaveAnnotBtn.setEnabled(False)
        self.additionMode = False
        self.newParamsGB.setEnabled(False)




    def setRootLayoutSizes(self, sizes):
        self.rootLayout.setSizes(sizes)


    def viewParameter(self, parameter):
        row = -1
        for row, param in enumerate(self.paramListModel.parameterList):
            if param.id == parameter.id:
                break
        assert(row > -1)
        self.paramListTblWdg.selectRow(row)

        

    @QtCore.Slot(object, str)
    def newParamTypeSelected(self, paramName):
        self.requiredTagsListModel.clear()
        self.requiredTagsListModel.refresh()

        paramType  = getParameterTypeFromName(paramName)
        if paramType is None:
            raise ValueError("Parameter type with name '" + paramName + "' was not found.")

        for reqTag in paramType.requiredTags:
            self.requiredTagsListModel.addTag(reqTag.id, reqTag.name, reqTag.id, reqTag.name)

        self.requiredTagsListModel.refresh()


    def buildRequiredTagsGB(self):

        # Widgets            
        self.requireTagGB = QtGui.QGroupBox("Required tag categories", self)

        self.requiredTagsListTblWdg      = RequiredTagsTableView() 
        self.requiredTagsListModel       = RequiredTagsListModel(self)
        self.requiredTagsListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.requiredTagsListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.requiredTagsListTblWdg.setModel(self.requiredTagsListModel)
        self.requiredTagsListTblWdg.setColumnWidth(0, 200)
        self.requiredTagsListTblWdg.setColumnWidth(1, 200)

        # Layout
        requiredTagLayout = QtGui.QGridLayout(self.requireTagGB)
        requiredTagLayout.addWidget(self.requiredTagsListTblWdg, 0, 0, 4, 1)


    def newParameter(self):
        self.resultTypeCbo.setCurrentIndex(0)
        self.paramModStack.currentWidget().newParameter()
        
        self.singleValueParamWgt.newParameter()
        self.functionParamWgt.newParameter()
        self.traceParamWgt.newParameter()       
        
        self.newParamsGB.setEnabled(True)
        self.paramListTblWdg.clearSelection()

        self.newParamBtn.setEnabled(False)
        self.deleteParamBtn.setEnabled(False)
        self.paramSaveAnnotBtn.setEnabled(True)

        self.isExpProp.setChecked(False)


    def saveParameter(self):

        relationship = self.relationWgt.getRelationship()
        
        # Get the ID of the modified parameter if we are modifying an existing
        # parameters        
        if len(self.paramListTblWdg.selectionModel().selectedRows()) != 0:
            selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
            paramId = self.parent.currentAnnotation.parameters[selectedRow].id        
        else:
            paramId = None
        
        param = self.paramModStack.currentWidget().saveParameter(relationship, paramId)

        if not param is None:
            param.requiredTags             = self.requiredTagsListModel.getRequiredTags()
            print(param.requiredTags) 
            param.isExperimentProperty     = self.isExpProp.isChecked()

            selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
            # Even when there is no selection, selectedRow can take a zero value. This "if" 
            # controls for that.
            if len(self.paramListTblWdg.selectionModel().selectedRows()) == 0:
                selectedRow = -1

            if selectedRow >= 0:
                self.parent.currentAnnotation.parameters[selectedRow] = param
            else:
                self.parent.currentAnnotation.parameters.append(param)

            self.additionMode = False
            nbParams = len(self.parent.currentAnnotation.parameters)
            self.parent.saveAnnotation()            

            if selectedRow < 0 :
                selectedRow = nbParams-1
            self.paramListTblWdg.selectRow(selectedRow)
            self.loadRow(selectedRow)     



    def deleteParameter(self):
        selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
        del self.parent.currentAnnotation.parameters[selectedRow]
        self.parent.saveAnnotation()
        self.refreshModelingParameters()


    def refreshModelingParameters(self):
        selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
        self.loadModelingParameter(selectedRow)


    def loadModelingParameter(self, row = None):
        """
         Call when a new annotation has been selected so that all the modeling parameters
         associated with this annotation are loaded in the parameter list. 
        """

        self.requiredTagsListModel.clear()
        self.requiredTagsListModel.refresh()

        if self.parent.currentAnnotation is None:
            self.paramListModel.parameterList = []
        else:
            self.paramListModel.parameterList = self.parent.currentAnnotation.parameters

            aRowIsSelected = not row is None
            if aRowIsSelected:
                if row < 0:
                    noRowToLoad = self.paramListTblWdg.model().rowCount()-row
                else:
                    noRowToLoad = row
            else:
                ## No rows are selected
                noRowToLoad = -1
            
            self.loadRow(noRowToLoad)
            self.newParamBtn.setEnabled(True)
            self.deleteParamBtn.setEnabled(aRowIsSelected)
            self.paramSaveAnnotBtn.setEnabled(aRowIsSelected)
            self.paramModStack.currentWidget().loadModelingParameter(row)
            self.relationWgt.loadModelingParameter(row)

            self.newParamsGB.setEnabled(aRowIsSelected)
        
        self.paramListModel.refresh()


    def loadRow(self, selectedRow = None):
        """
         Called when a row has been selected in the table listing all the modeling parameters.
         It update the interface with the values associated with this specific parameter.
        """

        def clear():
            self.requiredTagsListModel.clear()
            self.paramModStack.currentWidget().loadRow(None)
            self.relationWgt.clear()        
            self.paramListTblWdg.clearSelection()

        if selectedRow is None:
            selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
        
        if self.parent.currentAnnotation is None:        
            clear()
            return
        
        if selectedRow < 0 or selectedRow >= len(self.parent.currentAnnotation.parameters) :
            clear()
            return
            
        currentParameter = self.parent.currentAnnotation.parameters[selectedRow]
    
        self.newParamBtn.setEnabled(True)
        self.deleteParamBtn.setEnabled(True)
        self.paramSaveAnnotBtn.setEnabled(True)

        if currentParameter.description.type == "pointValue":
            self.resultTypeCbo.setCurrentIndex(0)
            self.paramModStack.setCurrentIndex(0)
        elif currentParameter.description.type == "function": 
            self.resultTypeCbo.setCurrentIndex(1)
            self.paramModStack.setCurrentIndex(1)
        elif currentParameter.description.type == "numericalTrace": 
            self.resultTypeCbo.setCurrentIndex(2)
            self.paramModStack.setCurrentIndex(2)
        else:
            raise ValueError("Type of parameter description " + currentParameter.description.type + " is invalid.")

        self.paramModStack.currentWidget().loadRow(currentParameter)
        self.relationWgt.loadRow(currentParameter)
        self.isExpProp.setChecked(currentParameter.isExperimentProperty)

        ## UPDATING REQUIRED TAGS
        self.requiredTagsListModel.clear()
        for tag in currentParameter.requiredTags:        
            self.requiredTagsListModel.addTag(tag.rootId, self.parent.dicData[tag.rootId], tag.id, tag.name)
        self.requiredTagsListModel.refresh()

        self.newParamsGB.setEnabled(True)


    def selectedParameterChanged(self, selected, deselected):
        if len(selected.indexes()) == 0:
            return
        if self.additionMode:
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Cancellation")
            msgBox.setText("Are you sure you want to cancel the addition of the new parameter being edited? If not, say no and then hit 'Save' to save this new parameter.")
            msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            msgBox.setDefaultButton(QtGui.QMessageBox.No)
            if msgBox.exec_() == QtGui.QMessageBox.Yes:
                self.additionMode = False
                self.loadRow()
            else:
                #self.paramListTblWdg.selectRow(-1)
                self.paramListTblWdg.clearSelection()
        else:
            self.loadRow()






class ParameterListModel(QtCore.QAbstractTableModel):

    def __init__(self, parent, parameterList = [], header = ['ID', 'Type', 'Description'], *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.parameterList = parameterList
        self.header = header
        self.nbCol = len(header)

    def rowCount(self, parent=None):
        return len(self.parameterList)

    def columnCount(self, parent=None):
        return self.nbCol 


    def getSelectedParameter(self, selection):

        if isinstance(selection, list):
            if selection == []:
                return None
            elif isinstance(selection[0], QtCore.QModelIndex):
                index = selection[0]
        else:
            if selection.at(0) is None:
                return None
            index = selection.at(0).indexes()[0]
        return self.parameterList[index.row()]



    def getByIndex(self, param, ind):
        if ind == 0:
            return param.id
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

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != QtCore.Qt.DisplayRole:
            return None

        return self.getByIndex(self.parameterList[index.row()], index.column())

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
        reverse = (order == QtCore.Qt.DescendingOrder)
        self.annotationList = sorted(self.parameterList, key=lambda x: x.getByIndex(col), reverse = reverse) 
        self.emit(QtCore.SIGNAL("layoutChanged()"))

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))




