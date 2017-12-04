#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtCore import Slot, Qt
from PySide.QtGui import (QAbstractItemView, QSortFilterProxyModel, QWidget,
                          QTableView, QVBoxLayout, QLineEdit, QFormLayout)

from nat.zotero_wrap import ZoteroWrap
from neurocurator.zotero_edition import ZoteroReferenceDialog
from neurocurator.zotero_model import ZoteroTableModel
from neurocurator.zotero_thread import ZoteroRefreshThread


class ZoteroTableWidget(QWidget):

    def __init__(self, settings, work_dir, check_id_fct, annotations_path, parent=None):
        super().__init__(parent)
        # FIXME Delayed refactoring of check_id_fct and annotations_path.

        # Variables section.

        library_id = settings["libraryID"]
        library_type = settings["libraryType"]
        api_key = settings["apiKey"]

        # Widgets section.

        self.zotero = ZoteroWrap(library_id, library_type, api_key, work_dir)

        model = ZoteroTableModel(self.zotero, check_id_fct, annotations_path)
        model.load()

        # NB: The thread does not begin executing until start() is called.
        self.refresh_thread = ZoteroRefreshThread(model, self)

        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setDynamicSortFilter(True)
        proxy_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
        proxy_model.setFilterKeyColumn(-1)  # NB: All columns.

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

        self.filter_edit = FilterEdit(self.view)

        # Layouts section.

        header_layout = QFormLayout()
        header_layout.addRow("Filter:", self.filter_edit)
        header_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        header_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        header_layout.setLabelAlignment(Qt.AlignLeft)
        header_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)

        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self.view)
        self.setLayout(main_layout)

        # Signals section.

        self.filter_edit.textChanged.connect(proxy_model.setFilterFixedString)
        self.refresh_thread.started.connect(self.refresh_started)
        self.refresh_thread.finished.connect(self.refresh_finished)

    # def __del__(self):
    #     # FIXME Delayed refactoring. Not called when application is closed. Incorrect parent use?
    #     # NB: Exiting the program when another thread is still busy is a programming error.
    #     # NB: Call QThread::quit() if the thread has an event loop.
    #     print("DEBUG: ZoteroTableWidget.__del__()")
    #     # TODO Display an information dialog.
    #     self.refresh_thread.wait()
    #     print("DEBUG: ZoteroRefreshThread.wait() returned")

    # Slots section.

    @Slot()
    def refresh_database(self):
        # NB: If the thread is already running, this function does nothing.
        self.refresh_thread.start()

    @Slot()
    def refresh_started(self):
        # TODO Display an information dialog.
        # Disable handling of keyboard/mouse events to ensure a thread-safe refresh.
        self.setEnabled(False)

    @Slot()
    def refresh_finished(self):
        # Enable handling of keyboard/mouse events.
        self.setEnabled(True)

    @Slot()
    def add_reference(self):
        dialog = ZoteroReferenceDialog(self.zotero.reference_templates, self)
        dialog.setWindowTitle("Zotero reference creation")
        dialog.select_reference_type("journalArticle")
        # NB: exec() always pops up the dialog as modal.
        if dialog.exec():
            reference_data = dialog.reference_data()
            # TODO Implement an offline mode. Catch PyZoteroError.
            reference_key = self.zotero.create_distant_reference(reference_data)
            # TODO Implement an offline mode. Catch PyZoteroError.
            reference = self.zotero.get_reference(reference_key)
            self.view.model().sourceModel().add_reference(reference)

    @Slot()
    def edit_reference(self):
        selected = self.view.selectionModel().currentIndex()
        if selected.isValid():
            row = self.view.model().mapToSource(selected).row()

            # # FIXME DEBUG during refactoring.
            # print("\n")
            # print("TITLE: " + self.zotero.reference_title(row))
            # print("SOURCE ROW NB: " + str(row))
            # # /FIXME DEBUG during refactoring.

            reference_key = self.zotero.reference_key(row)
            # TODO Refresh local when distant is different and "Cancel" clicked.
            # TODO Display an information dialog when local and distant are different.
            # TODO Implement an offline mode. Catch PyZoteroError.
            reference = self.zotero.get_reference(reference_key)
            dialog = ZoteroReferenceDialog(self.zotero.reference_templates, self)
            dialog.setWindowTitle("Zotero reference edition")
            dialog.load_reference_data(reference["data"])
            # NB: exec() always pops up the dialog as modal.
            if dialog.exec():
                reference["data"] = dialog.reference_data()
                # TODO Implement an offline mode. Catch PyZoteroError.
                self.zotero.update_distant_reference(reference)
                # TODO Implement an offline mode. Catch PyZoteroError.
                reference = self.zotero.get_reference(reference_key)
                self.view.model().sourceModel().update_reference(row, reference)
        else:
            # TODO Display an information dialog.
            raise ValueError("No row selected for edition.")


class FilterEdit(QLineEdit):
    # QTableView::setSelectionMode(QAbstractItemView.NoSelection) without or
    # with QTableView::clearSelection() is not sufficient to disable the
    # selection of a row during QSortFilterProxyModel::setFilterFixedString().
    # The purpose of this subclassing is to disable this automatic selection.

    def __init__(self, view, parent=None):
        super().__init__(parent)
        self._view = view

    # Qt interface implementation section.

    def focusInEvent(self, focus_event):
        # QItemSelectionModel::clearSelection() is not sufficient.
        # QItemSelectionModel::clearSelection() emits signals, reset() not.
        self._view.selectionModel().reset()
        super().focusInEvent(focus_event)
