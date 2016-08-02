#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Contributed libraries imports
from PySide import QtGui

from nat.annotation import getParametersForPub
from nat.utils import Id2FileName
from nat.modelingParameter import ParamRef

#from modelingParameter import ExperimentProperty
#from itemDelegates import ExpPropertiesDelegate
from .paramFunctionWgt import ParameterInstanceTableView, ParameterInstanceListModel

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
            
        parameters = getParametersForPub(self.parent.dbPath, Id2FileName(self.parent.currentAnnotation.pubId))
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

