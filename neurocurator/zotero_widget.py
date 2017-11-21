#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtCore import Slot
from PySide.QtGui import (QAbstractItemView, QSortFilterProxyModel, QWidget,
                          QTableView, QVBoxLayout)

from nat.zotero_wrap import ZoteroWrap
from neurocurator.zotero_model import ZoteroTableModel
from neurocurator.zotero_thread import ZoteroRefreshThread


class ZoteroTableWidget(QWidget):

    def __init__(self, settings, work_dir, check_id_fct, annotations_path, window, parent=None):
        super().__init__(parent)
        # FIXME Delayed refactoring of check_id_fct + annotations_path + window.
        self.window = window

        # Variables section.

        library_id = settings["libraryID"]
        library_type = settings["libraryType"]
        api_key = settings["apiKey"]

        # Widgets sections.

        wrap = ZoteroWrap(library_id, library_type, api_key, work_dir)

        model = ZoteroTableModel(wrap, check_id_fct, annotations_path)
        model.load()

        # FIXME NB: Don't update source through proxy when dynamicSortFilter is true.
        # FIXME NB: To convert source QModelIndexes to sorted/filtered model
        # FIXME indexes or vice versa, use mapToSource(), mapFromSource(),
        # FIXME mapSelectionToSource(), and mapSelectionFromSource().
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setDynamicSortFilter(True)

        # FIXME Use signals elsewhere instead of references to the view.
        self.view = QTableView(self)
        self.view.setModel(proxy_model)
        self.view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.view.setSelectionMode(QAbstractItemView.SingleSelection)
        self.view.setCornerButtonEnabled(False)
        # NB: Triggers a call to sortByColumn() which sorts by the first column.
        self.view.setSortingEnabled(True)
        self.view.setWordWrap(False)
        self.view.verticalHeader().hide()

        # NB: The thread does not begin executing until start() is called.
        self._refresh_thread = ZoteroRefreshThread(model, self)

        # Layouts section.

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        # Signals section.

        # FIXME Delayed refactoring. Move into the dedicated QTabWidget object.
        self.view.doubleClicked.connect(window.changeTagToAnnotations)
        selection_model = self.view.selectionModel()  # Necessary.
        selection_model.currentRowChanged.connect(window.paperSelectionChanged)

        self._refresh_thread.finished.connect(self.refresh_finished)

    def __del__(self):
        # FIXME NOT CALLED WHEN THE APPLICATION IS CLOSED! Fix parent use (?).
        # NB: Exiting the program when another thread is still busy is a programming error.
        # NB: Call QThread::quit() if the thread has an event loop.
        print("DEBUG: ZoteroTableWidget.__del__()")
        self._refresh_thread.wait()  # TODO Display an information dialog.
        print("DEBUG: ZoteroRefreshThread.wait() returned")

    # Slots sections.

    @Slot()
    def refresh(self):
        # TODO Display an information dialog about the deactivation.
        # Disable handling of keyboard/mouse events to ensure a thread-safe refresh.
        self.setEnabled(False)
        # FIXME Delayed refactoring. Use QStatusBar slots.
        self.window.statusLabel.setText("Refreshing the Zotero database...")
        # NB: If the thread is already running, this function does nothing.
        self._refresh_thread.start()

    @Slot()
    def refresh_finished(self):
        # Enable handling of keyboard and mouse events.
        self.setEnabled(True)
        # FIXME Delayed refactoring. Use QStatusBar slots with a timeout.
        self.window.statusLabel.setText("Zotero database refreshing complete.")
