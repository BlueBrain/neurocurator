#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtCore import QModelIndex, pyqtSignal, pyqtSlot, QAbstractTableModel, Qt
from PyQt5.QtWidgets import (QMessageBox, QGridLayout, QAbstractItemView,
                             QGroupBox, QSplitter, QVBoxLayout, QLabel,
                             QHBoxLayout, QStackedWidget, QCheckBox, QComboBox,
                             QTableView, QWidget, QPushButton)

from nat.modelingParameter import (getParameterTypeFromName,
                                   getParameterTypeNameFromID,
                                   getParameterTypeFromID)
from nat.ontoManager import OntoManager
from nat.tag import RequiredTag
from nat.tagUtilities import nlx2ks
from .itemDelegates import ReqTagDelegate
from .paramFunctionWgt import ParamFunctionWgt
from .paramRelationWgt import ParamRelationWgt
from .paramTraceWgt import ParamTraceWgt
from .paramValueWgt import ParamValueWgt


class RequiredTagsTableView(QTableView):

    setReqTags = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reqTagDelegate = ReqTagDelegate(self)
        self.setItemDelegateForColumn(1, self.reqTagDelegate)
        ontoMng = OntoManager()
        self.treeData = ontoMng.trees 
        self.dicData = ontoMng.dics
        self.reqTagDelegate.cboNeedPopulation.connect(self.setReqTags)

    def setReqTags(self, tagName):

        try:
            tagId = list(self.dicData.keys())[list(self.dicData.values()).index(tagName)]
        except ValueError:
            ontoMng = OntoManager(recompute=True)      
            self.treeData = ontoMng.trees 
            self.dicData = ontoMng.dics    
            tagId = list(self.dicData.keys())[list(self.dicData.values()).index(tagName)]
            
        
        if not tagId in self.treeData:
            raise ValueError("The term id " + tagId + " was not specified as an ontological root.")

        self.reqTagDelegate.addItems(list(self.treeData[tagId].values()))




class RequiredTagsListModel(QAbstractTableModel):

    def __init__(self, colHeader = ['Required categories', 'Selected tag'], parent=None):
        super().__init__(parent)
        self.colHeader = colHeader
        self.nbCol = len(colHeader)
        self.requiredTagsIds = []
        self.requiredTagsNames = []
        self.selectedTagsIds = []
        self.selectedTagsNames = []
        ontoMng = OntoManager()
        self.treeData = ontoMng.trees 
        self.dicData = ontoMng.dics


    def rowCount(self, parent=QModelIndex()):
        return len(self.requiredTagsNames)

    def columnCount(self, parent=QModelIndex()):
        return self.nbCol 

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if not role in [Qt.DisplayRole, Qt.UserRole]:
            return None

        if index.column() == 0:
            return self.requiredTagsNames[index.row()]
        elif index.column() == 1:
            return self.selectedTagsNames[index.row()]
        else:
            return None


    def setData(self, index, value, role=Qt.DisplayRole):
        if value is None:
            value = ""

        if index.column() == 0:
            self.requiredTagsNames[index.row()] = value
            tagId = list(self.dicData.keys())[list(self.dicData.values()).index(value)]            
            self.requiredTagsIds[index.row()] = tagId
            
        elif index.column() == 1:
            if self.checkTagValidity(index.row(), value):
                self.selectedTagsNames[index.row()] = value
                tagId = list(self.dicData.keys())[list(self.dicData.values()).index(value)]    
                self.selectedTagsIds[index.row()] = tagId

    def checkTagValidity(self, row, tagName):

        tagId = self.requiredTagsIds[row]

        if not tagId in self.treeData:    
            ontoMng = OntoManager(recompute=True)      
            self.treeData = ontoMng.trees 
            self.dicData = ontoMng.dics            
            if not tagId in self.treeData:                
                raise ValueError("Tag '" + tagId + "' is not a treeData root. TreeData roots are the following:" + str(list(self.treeData.keys())))

        return tagName in list(self.treeData[tagId].values())


    def flags(self, index):
        if index.column() == 0:
            result = super().flags(index)
            result &= ~Qt.ItemIsEditable
            return result
        else:
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.colHeader[section]        
        return None

    def refresh(self):
        self.layoutChanged.emit()

    def addTag(self, requiredTagId, requiredTagName, selectedTagId, selectedTagName):
        self.requiredTagsNames.append(requiredTagName)
        self.requiredTagsIds.append(requiredTagId)
        self.selectedTagsNames.append(selectedTagName)
        self.selectedTagsIds.append(selectedTagId)
        self.refresh()

    def clear(self):
        self.requiredTagsNames = []
        self.requiredTagsIds = []
        self.selectedTagsNames = []
        self.selectedTagsIds = []
        self.refresh()

    def getRequiredTags(self):
        return [RequiredTag(id, name, rootId) for id, name, rootId in zip(self.selectedTagsIds, self.selectedTagsNames, self.requiredTagsIds)]





class ParamModWgt(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)


        ### Parameters section

        self.existingParamsGB = QGroupBox("Existing parameters", self)

        buttonWidget = QWidget(self)

        self.paramSaveAnnotBtn = QPushButton("Save")
        self.paramSaveAnnotBtn.setEnabled(False)
        self.paramSaveAnnotBtn.clicked.connect(self.saveParameter)

        self.deleteParamBtn = QPushButton("Delete")
        self.deleteParamBtn.setEnabled(False)
        self.deleteParamBtn.clicked.connect(self.deleteParameter)

        self.newParamBtn = QPushButton("New")
        self.newParamBtn.setEnabled(True)
        self.newParamBtn.clicked.connect(self.newParameter)

        buttonLayout = QVBoxLayout(buttonWidget)
        buttonLayout.addWidget(self.paramSaveAnnotBtn)
        buttonLayout.addWidget(self.deleteParamBtn)
        buttonLayout.addWidget(self.newParamBtn)

        self.paramListModel = ParameterListModel(parent=self)

        self.paramListTblWdg = QTableView()
        self.paramListTblWdg.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.paramListTblWdg.setSelectionMode(QAbstractItemView.SingleSelection)
        self.paramListTblWdg.setModel(self.paramListModel)
        self.paramListTblWdg.setColumnWidth(0, 150)
        self.paramListTblWdg.setColumnWidth(1, 350)

        selectionModel = self.paramListTblWdg.selectionModel()
        selectionModel.selectionChanged.connect(self.selectedParameterChanged)  # FIXME External selectedParameterChanged.

        existGrid = QHBoxLayout(self.existingParamsGB)
        existGrid.addWidget(buttonWidget)
        existGrid.addWidget(self.paramListTblWdg)


        ### Parameter section



        ###


        self.main_window = parent

        self.buildRequiredTagsGB()

        # Widgets


        self.relationWgt = ParamRelationWgt(parent)
        self.newParamsGB = QGroupBox("Parameter details", self)
        self.resultTypeCbo = QComboBox(self)
        self.isExpProp = QCheckBox("is an experimental property", self)

        self.resultTypeCbo.addItems(["point value", "function", "numerical trace"])
        
        self.singleValueParamWgt = ParamValueWgt(parent)
        self.functionParamWgt = ParamFunctionWgt(parent)
        self.traceParamWgt = ParamTraceWgt(parent)

        self.functionParamWgt.mainWgt = self

        self.paramModStack = QStackedWidget(self)
        self.paramModStack.addWidget(self.singleValueParamWgt)
        self.paramModStack.addWidget(self.functionParamWgt)
        self.paramModStack.addWidget(self.traceParamWgt)

        # Signals

        self.resultTypeCbo.currentIndexChanged.connect(self.paramModStack.setCurrentIndex)
        self.singleValueParamWgt.paramTypeSelected.connect(self.newParamTypeSelected)
        self.functionParamWgt.paramTypeSelected.connect(self.newParamTypeSelected)
        self.traceParamWgt.paramTypeSelected.connect(self.newParamTypeSelected)

        # Layout

        newGrid = QGridLayout(self.newParamsGB)
        newGrid.addWidget(QLabel("Result type"), 0, 0)
        newGrid.addWidget(self.resultTypeCbo, 0, 1)
        newGrid.addWidget(self.isExpProp, 0, 2)
        
        newGrid.addWidget(self.paramModStack, 1, 0, 1, 3)
        newGrid.addWidget(self.relationWgt, 1, 3)

        # Initial behavior
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

        

    @pyqtSlot(str)
    def newParamTypeSelected(self, paramName):
        self.requiredTagsListModel.clear()
        self.requiredTagsListModel.refresh()

        paramType = getParameterTypeFromName(paramName)
        if paramType is None:
            raise ValueError("Parameter type with name '" + paramName + "' was not found.")

        for reqTag in paramType.requiredTags:
            self.requiredTagsListModel.addTag(reqTag.id, reqTag.name, reqTag.id, reqTag.name)

        self.requiredTagsListModel.refresh()


    def buildRequiredTagsGB(self):

        # Widgets            
        self.requireTagGB = QGroupBox("Required tag categories", self)

        self.requiredTagsListTblWdg = RequiredTagsTableView() 
        self.requiredTagsListModel = RequiredTagsListModel(parent=self)
        self.requiredTagsListTblWdg.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.requiredTagsListTblWdg.setSelectionMode(QAbstractItemView.SingleSelection)
        self.requiredTagsListTblWdg.setModel(self.requiredTagsListModel)
        self.requiredTagsListTblWdg.setColumnWidth(0, 200)
        self.requiredTagsListTblWdg.setColumnWidth(1, 200)

        # Layout
        requiredTagLayout = QGridLayout(self.requireTagGB)
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
            paramId = self.main_window.currentAnnotation.parameters[selectedRow].id
        else:
            paramId = None
        
        param = self.paramModStack.currentWidget().saveParameter(relationship, paramId)

        if not param is None:
            param.requiredTags = self.requiredTagsListModel.getRequiredTags()
            param.isExperimentProperty = self.isExpProp.isChecked()

            selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
            # Even when there is no selection, selectedRow can take a zero value. This "if" 
            # controls for that.
            if len(self.paramListTblWdg.selectionModel().selectedRows()) == 0:
                selectedRow = -1

            if selectedRow >= 0:
                self.main_window.currentAnnotation.parameters[selectedRow] = param
            else:
                self.main_window.currentAnnotation.parameters.append(param)

            self.additionMode = False
            nbParams = len(self.main_window.currentAnnotation.parameters)
            self.main_window.saveAnnotation()

            if selectedRow < 0 :
                selectedRow = nbParams-1
            self.paramListTblWdg.selectRow(selectedRow)
            self.loadRow(selectedRow)     



    def deleteParameter(self):
        selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
        del self.main_window.currentAnnotation.parameters[selectedRow]
        self.main_window.saveAnnotation()
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

        if self.main_window.currentAnnotation is None:
            self.paramListModel.parameterList = []
        else:
            self.paramListModel.parameterList = self.main_window.currentAnnotation.parameters

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
        
        def nlxCheck(id):
            if id in nlx2ks:
                return nlx2ks[id]
            return id
            
        def clear():
            self.requiredTagsListModel.clear()
            self.paramModStack.currentWidget().loadRow(None)
            self.relationWgt.clear()        
            self.paramListTblWdg.clearSelection()

        if selectedRow is None:
            selectedRow = self.paramListTblWdg.selectionModel().currentIndex().row()
        
        if self.main_window.currentAnnotation is None:
            clear()
            return
        
        if selectedRow < 0 or selectedRow >= len(self.main_window.currentAnnotation.parameters) :
            clear()
            return
            
        currentParameter = self.main_window.currentAnnotation.parameters[selectedRow]
    
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
            self.requiredTagsListModel.addTag(tag.rootId, self.main_window.dicData[tag.rootId], tag.id, tag.name)
        
        ## Adding new required tags that may have been specified since the 
        ## creation of this parameter instance.
        parameterType = getParameterTypeFromID(currentParameter.typeId)
        reqTags = {reqTag.rootId:reqTag for reqTag in parameterType.requiredTags}
        for reqTagRootId, reqTag in reqTags.items():
            #print(nlxCheck(reqTagRootId), [nlxCheck(tag.rootId) for tag in currentParameter.requiredTags])
            if not nlxCheck(reqTagRootId) in [nlxCheck(tag.rootId) for tag in currentParameter.requiredTags]:
                self.requiredTagsListModel.addTag(reqTag.rootId, self.main_window.dicData[reqTag.rootId], reqTag.id, reqTag.name)
            
        self.requiredTagsListModel.refresh()

        self.newParamsGB.setEnabled(True)


    def selectedParameterChanged(self, selected, deselected):
        if len(selected.indexes()) == 0:
            return
        if self.additionMode:
            msgBox = QMessageBox(self)
            msgBox.setWindowTitle("Cancellation")
            msgBox.setText("Are you sure you want to cancel the addition of the new parameter being edited? If not, say no and then hit 'Save' to save this new parameter.")
            msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgBox.setDefaultButton(QMessageBox.No)
            if msgBox.exec_() == QMessageBox.Yes:
                self.additionMode = False
                self.loadRow()
            else:
                #self.paramListTblWdg.selectRow(-1)
                self.paramListTblWdg.clearSelection()
        else:
            self.loadRow()


class ParameterListModel(QAbstractTableModel):

    def __init__(self, parameterList = [], header = ['ID', 'Type', 'Description'], parent=None):
        super().__init__(parent)
        self.parameterList = parameterList
        self.header = header
        self.nbCol = len(header)

    def rowCount(self, parent=QModelIndex()):
        return len(self.parameterList)

    def columnCount(self, parent=QModelIndex()):
        return self.nbCol 


    def getSelectedParameter(self, selection):

        if isinstance(selection, list):
            if selection == []:
                return None
            elif isinstance(selection[0], QModelIndex):
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

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        return self.getByIndex(self.parameterList[index.row()], index.column())

    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    def sort(self, col, order=Qt.AscendingOrder):
        # Sort table by given col number col.
        self.layoutAboutToBeChanged.emit()
        reverse = (order == Qt.DescendingOrder)
        self.annotationList = sorted(self.parameterList, key=lambda x: x.getByIndex(col), reverse = reverse)
        self.layoutChanged.emit()

    def refresh(self):
        self.layoutChanged.emit()
