#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

from PySide import QtGui, QtCore

class TreeModel(QtCore.QAbstractItemModel):

    def __init__(self, tree):
        super(TreeModel, self).__init__()
        self.__tree = tree
        if len(tree):
            self.__current = tree[0]


    def flags(self, index):
        flag = QtCore.Qt.ItemIsEnabled
        if index.isValid():
            flag |= QtCore.Qt.ItemIsSelectable
        return flag


    def index(self, row, column, parent=QtCore.QModelIndex()):
        if parent.isValid():
            node = parent.internalPointer().children[row]
        else:
            if not len(self.__tree):
                return
            node = self.__tree[row]
        return self.__createIndex(row, column, node)


    def parent(self, index):
        node = QtCore.QModelIndex()
        if index.isValid():
            nodeS = index.internalPointer()
            parent = nodeS.parent
            if parent is not None:
                node = self.__createIndex(parent.position(), 0, parent)
        return node


    def rowCount(self, index=QtCore.QModelIndex()):
        count = len(self.__tree)
        node = index.internalPointer()
        if node is not None:
            count = len(node.children)
        return count


    def columnCount(self, index=QtCore.QModelIndex()):
        return 1


    def data(self, index, role=QtCore.Qt.DisplayRole):
        data = None
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            node = index.internalPointer()
            data = node.txt

        if role == QtCore.Qt.UserRole:
            node = index.internalPointer()
            data = node.id

        return data


    def setData(self, index, value, role=QtCore.Qt.DisplayRole):
        result = True
        if role == QtCore.Qt.EditRole and value != "":
            node = index.internalPointer()
            node.text = value
            result = True
        return result


    def __createIndex(self, row, column, node):

        if hasattr(node, "index"):
            if not node.index is None: 
                return node.index
        
        index = self.createIndex(row, column, node)
        node.index = index
        return node.index

    def headerData(self, section, orientation, role):
        return None





class TreeView(QtGui.QTreeView):

    def __init__(self, model, parent=None):
        super(TreeView, self).__init__(parent)
        self.__model = model
        self.setModel(model)

        self.header().hide() 

        index = self.__model.index(0, 0)
        if not index is None:
            self.setCurrentIndex(index)

