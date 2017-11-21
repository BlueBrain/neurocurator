#!/usr/bin/python3

__authors__ = ["Christian O'Reilly", "Pierre-Alexandre Fonta"]
__maintainer__ = "Pierre-Alexandre Fonta"

import sys

from PySide.QtGui import QApplication

from neurocurator.mainWin import Window

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.setGeometry(0, 0, 500, 1424)  # FIXME Temporary, for convenience.
    window.show()
    r = app.exec_()
    # FIXME See ZoteroTableWidget.__del__.
    window.zotero_widget._refresh_thread.wait()
    sys.exit(r)
