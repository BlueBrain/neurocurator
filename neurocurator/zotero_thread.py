__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtCore import QThread


class ZoteroRefreshThread(QThread):

    def __init__(self, zotero_model, parent=None):
        super().__init__(parent)
        # NB: Executes in the old thread.
        self._zotero_model = zotero_model

    def run(self):
        # NB: Executes in the new thread. Beware of accessing __init__() variables.
        # NB: Returning from this method will end the execution of the thread.
        # QMutex/QMutexLocker not needed if ZoteroTableModel is not modified.
        # QThread::exec() not needed if an event loop inside the thread is not needed.
        self._zotero_model.refresh()
