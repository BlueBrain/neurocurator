#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtWidgets import QHBoxLayout, QAbstractItemView, QWidget

from nat.annotation import getParametersForPub
from nat.paramDesc import ParamRef
from nat.utils import Id2FileName

from .paramFunctionWgt import ParameterInstanceTableView, ParameterInstanceListModel


class ExpPropWgt(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.main_window = parent

        # Widgets
        self.expPropertiesListTblWdg = ParameterInstanceTableView()
        self.expPropertiesListModel = ParameterInstanceListModel(parent=self)
        self.expPropertiesListTblWdg.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.expPropertiesListTblWdg.setSelectionMode(QAbstractItemView.SingleSelection)
        self.expPropertiesListTblWdg.setModel(self.expPropertiesListModel)

        self.expPropertiesListTblWdg.setColumnWidth(0, 20)
        self.expPropertiesListTblWdg.setColumnWidth(1, 150)
        self.expPropertiesListTblWdg.setColumnWidth(2, 500)

        # Signal
        self.expPropertiesListTblWdg.tableCheckBoxClicked.connect(self.propSelectionChanged)

        # Layout        
        expPropertiesLayout = QHBoxLayout(self)
        expPropertiesLayout.addWidget(self.expPropertiesListTblWdg)

    def fillingExpPropList(self, checkAll=False):
        if self.main_window.currentAnnotation is None:
            return
            
        parameters = getParametersForPub(self.main_window.dbPath, Id2FileName(self.main_window.currentAnnotation.pubId))
        parameters = [param for param in parameters if param.isExperimentProperty == True]

        if checkAll:
            selectedParams = [param.id for param in parameters]  
        elif self.main_window.currentAnnotation is None:
            selectedParams = []      
        else:
            selectedParams = [ref.instanceId for ref in self.main_window.currentAnnotation.experimentProperties]
            
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
        self.main_window.setNeedSaving()
