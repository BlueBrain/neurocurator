#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication, QLabel

from nat.tag import Tag


class TagWidget(QLabel):
    
    clicked = pyqtSignal(Tag)
    
    def __init__(self, tag, parent=None):
        super().__init__(tag.name, parent)
        self.tag = tag
        self.setAutoFillBackground(True)
        self.persist = False

    def mouseReleaseEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ShiftModifier:
            self.persist = not self.persist
        self.clicked.emit(self.tag)

    @property
    def persist(self):
        return self.__persist

    @persist.setter
    def persist(self, shouldPersist):
        if shouldPersist:
            ligthRed = QColor(255, 153, 153)
            palette = QPalette()
            palette.setColor(self.backgroundRole(),ligthRed)
            self.setPalette(palette)        
        else:
            #lightGreen = QtGui.QColor(191, 237, 135)
            palette = QPalette()
            palette.setColor(self.backgroundRole(), QColor(255, 255, 255))
            self.setPalette(palette)
        self.__persist = shouldPersist


