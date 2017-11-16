#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import sys

from PySide import QtGui
from neurocurator.mainWin import Window

if __name__ == '__main__':
	app = QtGui.QApplication(sys.argv)
	window = Window()
	window.app = app
	window.setGeometry(0, 0, 500, 1424)  # FIXME Temporary, for convenience.
	window.show()
	sys.exit(app.exec_())
