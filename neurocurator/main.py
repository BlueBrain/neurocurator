#!/usr/bin/python3

__authors__ = ["Christian O'Reilly", "Pierre-Alexandre Fonta"]
__maintainer__ = "Pierre-Alexandre Fonta"

import sys

from PySide.QtGui import QApplication

from neurocurator.mainWin import Window


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    # FIXME Temporary, for debug.
    window.setGeometry(0, 0, 500, 1424)
    window.show()
    sys.exit(app.exec_())
