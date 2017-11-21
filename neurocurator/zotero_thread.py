#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtCore import QThread


class ZoteroRefreshThread(QThread):

    def __init__(self, zotero_model, parent=None):
        # NB: Executes in the old thread.
        super().__init__(parent)
        self._zotero_model = zotero_model

    def run(self):
        # NB: Executes in the new thread. Beware of accessing __init__() variables.
        # NB: Returning from this method will end the execution of the thread.
        # QMutex/QMutexLocker not needed if ZoteroTableModel is not modified.
        # QThread::exec() not needed: event loop inside the thread not needed.
        self._zotero_model.refresh()
