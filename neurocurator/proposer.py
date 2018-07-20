#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtCore import QModelIndex, QAbstractTableModel, Qt


class PropositionTableModel(QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.header = ["value", "unit", "authors", "year", "journal"]
        self.nbCol = len(self.header)
        self.propositions = []

    def refreshData(self, annotatedInstances, modelingInstance):
        self.propositions = []

        for annotInstance in annotatedInstances:
            proposition = {"value": annotInstance.value,
                           "unit": annotInstance.unit,
                           "authors": "",
                           "year": "",
                           "journal": "",
                           "parameterInstance": annotInstance}
            self.propositions.append(proposition)

        self.layoutChanged.emit()

    def rowCount(self, parent=QModelIndex()):
        return len(self.propositions)

    def columnCount(self, parent=QModelIndex()):
        return self.nbCol 



    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None


        #if role == Qt.BackgroundRole:
        #    if self.checkIdFct(self.getID(index.row())):
        #        return QtGui.QBrush(QtGui.QColor(215, 214, 213), Qt.SolidPattern)
        #    else:
        #        return None

        if role == Qt.DisplayRole:
            try:
                return self.propositions[index.row()][self.header[index.column()]]
            except KeyError:
                return ""
        return None


    def headerData(self, col, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.header[col]
        return None

    #def sort(self, col, order):
    #    #sort table by given column number col
    #    self.layoutAboutToBeChanged.emit()
    #    reverse = (order == Qt.DescendingOrder)
    #    self.refList = sorted(self.refList, key=lambda x: self.getByIndex(x, col), reverse = reverse)
    #    self.layoutChanged.emit()

    def refresh(self):
        self.layoutChanged.emit()
