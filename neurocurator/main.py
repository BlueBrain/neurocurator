#!/usr/bin/env python3.4

__authors__ = ["Christian O'Reilly", "Pierre-Alexandre Fonta"]
__maintainer__ = "Pierre-Alexandre Fonta"

import sys

from PySide.QtGui import QApplication

from neurocurator.mainWin import Window


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    # FIXME DEBUG.
    # window.setGeometry(0, 0, 500, 1424)
    # /FIXME DEBUG.
    window.show()
    sys.exit(app.exec_())
