#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel
from PyQt5.QtWidgets import QTreeView


class TreeModel(QAbstractItemModel):

    def __init__(self, tree, parent=None):
        super().__init__(parent)

        self.__tree = tree

        if len(tree):
            self.__current = tree[0]

    def flags(self, index):
        flag = Qt.ItemIsEnabled
        if index.isValid():
            flag |= Qt.ItemIsSelectable
        return flag


    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid():
            node = parent.internalPointer().children[row]
        else:
            if not len(self.__tree):
                return
            node = self.__tree[row]
        return self.__createIndex(row, column, node)


    def parent(self, index):
        node = QModelIndex()
        if index.isValid():
            nodeS = index.internalPointer()
            parent = nodeS.parent
            if parent is not None:
                node = self.__createIndex(parent.position(), 0, parent)
        return node


    def rowCount(self, parent=QModelIndex()):
        count = len(self.__tree)
        node = parent.internalPointer()
        if node is not None:
            count = len(node.children)
        return count


    def columnCount(self, parent=QModelIndex()):
        return 1


    def data(self, index, role=Qt.DisplayRole):
        data = None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            node = index.internalPointer()
            data = node.txt

        if role == Qt.UserRole:
            node = index.internalPointer()
            data = node.id

        return data


    def setData(self, index, value, role=Qt.DisplayRole):
        result = True
        if role == Qt.EditRole and value != "":
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

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        return None





class TreeView(QTreeView):

    def __init__(self, model, parent=None):
        super().__init__(parent)

        self.__model = model
        self.setModel(model)

        self.header().hide()

        index = self.__model.index(0, 0)
        if not index is None:
            self.setCurrentIndex(index)
