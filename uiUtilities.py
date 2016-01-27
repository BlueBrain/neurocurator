#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
import sys
from PySide import QtGui, QtCore

paleGray = QtGui.QColor(215, 214, 213) 

def errorMessage(selfObj, title, message):
	msgBox = QtGui.QMessageBox(selfObj)
	msgBox.setWindowTitle(title)
	msgBox.setText(message)
	msgBox.exec_()


def disableTextWidget(widget):
	palette = QtGui.QPalette()
	palette.setColor(QtGui.QPalette.Base,paleGray)

	widget.setReadOnly(True)
	widget.setPalette(palette)


def enableTextWidget(widget):
	palette = QtGui.QPalette()
	palette.setColor(QtGui.QPalette.Base, QtCore.Qt.white)

	widget.setReadOnly(False)
	widget.setPalette(palette)


