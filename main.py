#!/usr/bin/python3

__author__ = "Christian O'Reilly"


import sys
from PySide import QtGui
from mainWin import Window


# This import is necessary because we are pickling TreeData object in
# the application. Without the import here, we get an AttributeError.
from qtNeurolexTree import TreeData

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	window = Window()
	window.app = app
	window.setGeometry(500, 300, 800, 500)
	window.showFullScreen()
	window.showMaximized()
	window.show()
	sys.exit(app.exec_())

