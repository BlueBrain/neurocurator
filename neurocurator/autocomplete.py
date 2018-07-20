from sys import platform as _platform

from PyQt5.QtCore import (pyqtSignal, QSortFilterProxyModel, QStringListModel,
                          QEvent, QRegExp, Qt)
from PyQt5.QtWidgets import QCompleter, QComboBox


class CustomQCompleter(QCompleter):
    """
    adapted from: http://stackoverflow.com/a/7767999/2156909
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.local_completion_prefix = ""
        self.source_model = None
        self.filterProxyModel = QSortFilterProxyModel(self)
        self.usingOriginalModel = False

    def setModel(self, strList): 
        self.source_model = QStringListModel(strList)
        self.filterProxyModel = QSortFilterProxyModel(self)
        self.filterProxyModel.setSourceModel(self.source_model)
        super().setModel(self.filterProxyModel)
        self.usingOriginalModel = True


    def updateModel(self):
        if not self.usingOriginalModel:
            self.filterProxyModel.setSourceModel(self.source_model)

        pattern = QRegExp(self.local_completion_prefix,
                                Qt.CaseInsensitive,
                                QRegExp.FixedString)

        self.filterProxyModel.setFilterRegExp(pattern)

    def splitPath(self, path):
        self.local_completion_prefix = path
        self.updateModel()
        if self.filterProxyModel.rowCount() == 0:
            self.usingOriginalModel = False
            self.filterProxyModel.setSourceModel(QStringListModel([path]))
            return [path]

        self.usingOriginalModel = True
        return []

class AutoCompleteEdit(QComboBox):

    enterKeyPressed = pyqtSignal(QComboBox)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(self.NoInsert)
        self.comp = CustomQCompleter(self)
        self.comp.setCompletionMode(QCompleter.PopupCompletion)
        self.setCompleter(self.comp)
        self.setEditText("")
        self.erase = False
        self.deactivateClearing = False

    def setModel(self, strList):
        self.clear()
        self.insertItems(0, strList)
        self.comp.setModel(strList)

    def focusInEvent(self, event):
        
    
        if _platform in ["linux", "linux2"]:
              # This behavior is the original one, which is fine in linux. On MacOS,
            # selecting an item change the value of the combobox and then set the focus on it
            # which was making this line erase the selected text.
            if not self.deactivateClearing :
                self.clearEditText()

        super().focusInEvent(event)


    def event(self, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Enter or event.key() == 16777220:
                # Enter (if event.key() == Qt.Key_Enter) does not work
                # for some reason
 
                self.deactivateClearing = True
                # make sure that the completer does not set the
                # currentText of the combobox to "" when pressing enter
                text = self.currentText()
                self.setCompleter(None)
                self.setEditText(text)
                self.setCompleter(self.comp)
                self.enterKeyPressed.emit(self)
                self.deactivateClearing = False
                
        eventReturn = super().event(event)
        return eventReturn
