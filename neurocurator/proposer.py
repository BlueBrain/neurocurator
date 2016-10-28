#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PySide import QtCore


class PropositionTableModel(QtCore.QAbstractTableModel):

    def __init__(self, *args):
        super(PropositionTableModel, self).__init__(*args)

        self.header = ["value", "unit", "authors", "year", "journal"]
        self.nbCol = len(self.header)
        self.propositions = []

    def refreshData(self, annotatedInstances, modelingInstance):
        self.propositions = []
        for annotInstance in annotatedInstances:
            proposition = {}
            proposition["value"]     = annotInstance.value
            proposition["unit"]     = annotInstance.unit
            proposition["authors"]     = ""
            proposition["year"]     = ""
            proposition["journal"]     = ""
            proposition["parameterInstance"] = annotInstance
            self.propositions.append(proposition)

        self.emit(QtCore.SIGNAL("layoutChanged()"))


    def rowCount(self, parent = None):
        return len(self.propositions)

    def columnCount(self, parent = None):
        return self.nbCol 



    def data(self, index, role):
        if not index.isValid():
            return None


        #if role == QtCore.Qt.BackgroundRole:
        #    if self.checkIdFct(self.getID(index.row())):
        #        return QtGui.QBrush(QtGui.QColor(215, 214, 213), QtCore.Qt.SolidPattern)
        #    else:
        #        return None

        if role == QtCore.Qt.DisplayRole:
            try:
                return self.propositions[index.row()][self.header[index.column()]]
            except KeyError:
                return ""
        return None


    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

    #def sort(self, col, order):
    #    #sort table by given column number col
    #    self.emit(QtCore.SIGNAL("layoutAboutToBeChanged()"))
    #    reverse = (order == QtCore.Qt.DescendingOrder)
    #    self.refList = sorted(self.refList, key=lambda x: self.getByIndex(x, col), reverse = reverse)
    #    self.emit(QtCore.SIGNAL("layoutChanged()"))

    def refresh(self):
        self.emit(QtCore.SIGNAL("layoutChanged()"))



