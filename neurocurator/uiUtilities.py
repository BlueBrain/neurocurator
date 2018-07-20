#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QMessageBox


paleGray = QColor(215, 214, 213)

def errorMessage(selfObj, title, message):
    msgBox = QMessageBox(selfObj)
    msgBox.setWindowTitle(title)
    msgBox.setText(message)
    msgBox.exec_()


def disableTextWidget(widget):
    palette = QPalette()
    palette.setColor(QPalette.Base,paleGray)

    widget.setReadOnly(True)
    widget.setPalette(palette)


def enableTextWidget(widget):
    palette = QPalette()
    palette.setColor(QPalette.Base, Qt.white)

    widget.setReadOnly(False)
    widget.setPalette(palette)


