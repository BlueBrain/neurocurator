#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QSize
from PyQt5.QtWidgets import (QLabel, QVBoxLayout, QAbstractItemView,
                             QListWidgetItem, QListWidget, QDialog, QTextEdit)


class TextEdit(QTextEdit):
    
    def __init__(self, no, parent=None):
        super().__init__(parent)
        self.no = no

    clicked = pyqtSignal(int)

    def mouseReleaseEvent(self, event):
        self.clicked.emit(self.no)


class MatchDlg(QDialog):

    def __init__(self, blocks, fileText, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Approximate matches")
        self.setGeometry(100, 300, 1000, 200)

        NContext = 30

        self.listWidget = QListWidget(self)

        for row, block in enumerate(blocks):
            item = QListWidgetItem()

            before = fileText[block["start"]-NContext:block["start"]]
            after = fileText[block["end"]:block["end"]+NContext]

            item.setSizeHint(QSize(1000, 50))
            textEdit = TextEdit(row, self)
            textEdit.insertHtml('{}<b>{}</b>{}'.format(before, block["candidate"], after))
            self.listWidget.addItem(item)
            self.listWidget.setItemWidget(item, textEdit)

            textEdit.clicked.connect(self.selectText)

        self.listWidget.showMaximized()

        self.listWidget.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.listWidget.setSelectionMode(QAbstractItemView.SingleSelection)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('The text to annotate has not been found. Similar entries are listed below. Please choose correct one.', self))
        layout.addWidget(self.listWidget)
        self.setLayout(layout)

        self.blocks = blocks
        self.chosenBlock = None

    @pyqtSlot(int)
    def selectText(self, row):
        self.chosenBlock = self.blocks[row]
        self.accept()
