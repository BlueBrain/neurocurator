#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtGui import (QAbstractItemView, QSortFilterProxyModel, QWidget,
                          QTableView, QVBoxLayout)

from nat.zotero_wrap import ZoteroWrap
from neurocurator.zotero_model import ZoteroTableModel


class ZoteroTableWidget(QWidget):

    def __init__(self, settings, work_dir, check_id_fct, annotations_path, window, parent=None):
        super().__init__(parent)
        # FIXME Delayed refactoring of check_id_fct + annotations_path + window.

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

        # FIXME Use elsewhere signals instead of references to the view.
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

        # Layouts section.

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        # Signals and slots section.

        self.view.doubleClicked.connect(window.changeTagToAnnotations)
        selection_model = self.view.selectionModel()  # Necessary.
        selection_model.currentRowChanged.connect(window.paperSelectionChanged)
