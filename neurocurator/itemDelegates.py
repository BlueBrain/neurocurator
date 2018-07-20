#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (QItemDelegate, QPushButton, QCheckBox,
                             QStyledItemDelegate, QLineEdit, QMessageBox,
                             QComboBox)

from nat.modelingParameter import getParameterTypes
from nat.values import unitIsValid, statisticList
from .autocomplete import AutoCompleteEdit


parameterTypes = getParameterTypes()


class ParamTypeCbo(AutoCompleteEdit):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setModel([paramType.name for paramType in parameterTypes])


class ButtonDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QPushButton in every
    cell of the column to which it's applied
    """

    def __init__(self, parent=None):
        # The parent is not an optional argument for the delegate as
        # we need to reference it in the paint method (see below)
        super().__init__(parent)
 
    def paint(self, painter, option, index):
        # This method will be called every time a particular cell is
        # in view and that view is changed in some way. We ask the 
        # delegates parent (in this case a table view) if the index
        # in question (the table cell) already has a widget associated 
        # with it. If not, create one with the text for this index and
        # connect its clicked signal to a slot in the parent view so 
        # we are notified when its used and can do something. 
        if not self.parent().indexWidget(index):
            button = QPushButton("delete", self.parent(), clicked=self.parent().cellButtonClicked)
            button.row = index.row()
            self.parent().setIndexWidget(index, button)


class CheckBoxDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning QPushButton in every
    cell of the column to which it's applied
    """

    def __init__(self, parent=None):
        # The parent is not an optional argument for the delegate as
        # we need to reference it in the paint method (see below)
        super().__init__(parent)
 
    def paint(self, painter, option, index):
        # This method will be called every time a particular cell is
        # in view and that view is changed in some way. We ask the 
        # delegates parent (in this case a table view) if the index
        # in question (the table cell) already has a widget associated 
        # with it. If not, create one with the text for this index and
        # connect its clicked signal to a slot in the parent view so 
        # we are notified when its used and can do something. 
        if not self.parent().indexWidget(index):
            checkBox = QCheckBox(parent=self.parent(), clicked=self.parent().checkBoxClicked)
            checkBox.row = index.row()
            self.parent().setIndexWidget(index, checkBox)
        else:
            checkBox = self.parent().indexWidget(index)

        checkBox.setChecked(self.parent().model().data(index))




class DoubleDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option=None, index=None):
        edit = QLineEdit(parent)
        edit.setValidator(QDoubleValidator())
        return edit


class UnitDelegate(QStyledItemDelegate):

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option=None, index=None):
        return QLineEdit(parent=parent)

    def setModelData(self, editor, model, index):
        if unitIsValid(editor.text()):
            model.setData(index, editor.text()) #, QtGui.Qt.EditRole)
        else:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Invalid parameter unit")
            msgBox.setText("This unit is not valid.")
            msgBox.exec_()             


class ComboBoxDelegate(QStyledItemDelegate):

    typeSelected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option=None, index=None):
        self.comboBox = QComboBox(parent)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)
        return self.comboBox

    def setEditorData(self, editor, index):
        self.comboBox = editor
        editor.blockSignals(True)
        cboIndex = -1
        if not index.model().data(index) is None:
            for i in range(editor.count()):
                if editor.itemText(i) == index.model().data(index):
                    cboIndex = i
                    break
        editor.setCurrentIndex(cboIndex)    
        editor.blockSignals(False)



    def setModelData(self, editor, model, index):
        self.comboBox = editor
        model.setData(index, self.comboBox.currentText()) #, QtGui.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)


    def currentIndexChanged(self):
        self.commitData.emit(self.sender())
        self.typeSelected.emit(self.comboBox.currentText())



class StatisticsDelegate(ComboBoxDelegate):

    def createEditor(self, parent, option=None, index=None):
        super().createEditor(parent, option, index)
        self.comboBox.addItems(statisticList)
        return self.comboBox


#class ExpPropertiesDelegate(ComboBoxDelegate):
#
#    def createEditor(self, parent, option=None, index=None):
#        super(ExpPropertiesDelegate, self).createEditor(parent, option, index)
#        self.comboBox.addItems(expPropertyStrList)
#        return self.comboBox


class ParamTypeDelegate(ComboBoxDelegate):

    def createEditor(self, parent, option=None, index=None):
        self.comboBox = ParamTypeCbo(parent)
        self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)
        return self.comboBox


class AutoCompleteDelegate(QStyledItemDelegate):

    #typeSelected = QtCore.Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

    def createEditor(self, parent, option=None, index=None):
        self.comboBox = AutoCompleteEdit(parent)
        #self.comboBox.currentIndexChanged.connect(self.currentIndexChanged)

        return self.comboBox

    """
    def setEditorData(self, editor, index):
        self.comboBox = editor
        editor.blockSignals(True)
        cboIndex = -1
        if not index.model().data(index) is None:
            for i in range(editor.count()):
                if editor.itemText(i) == index.model().data(index):
                    cboIndex = i
                    break
        editor.setCurrentIndex(cboIndex)    
        editor.blockSignals(False)
    """


    def setModelData(self, editor, model, index):
        self.comboBox = editor
        model.setData(index, self.comboBox.currentText()) #, QtGui.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)



class ReqTagDelegate(AutoCompleteDelegate):

    cboNeedPopulation = pyqtSignal(str)

    def createEditor(self, parent, option=None, index=None):
        super().createEditor(parent, option, index)
        model = index.model() 
        row = index.row()
        index = model.index(row, 0)
        paramTypeName = model.data(index, Qt.UserRole)
        self.initialText = model.data(model.index(row, 1))
        self.cboNeedPopulation.emit(paramTypeName)    
        #self.comboBox.enterKeyPressed.connect(self.enterKeyPressed)

        return self.comboBox


    def addItems(self, items):
        self.comboBox.setModel(items)




