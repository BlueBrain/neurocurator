#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtCore import QModelIndex, Qt, QAbstractTableModel
from PySide.QtGui import QColor, QBrush

from nat.annotationSearch import AnnotationSearch


class ZoteroTableModel(QAbstractTableModel):
    HEADERS = ["ID", "Title", "Creators", "Year", "Journal", "Annotations"]

    def __init__(self, zotero_wrap, check_id_fct, annotations_path, parent=None):
        super().__init__(parent)
        self.check_id_fct = check_id_fct  # FIXME Delayed refactoring.
        self.annotations_path = annotations_path  # FIXME Delayed refactoring.
        self._zotero_wrap = zotero_wrap
        self._annotation_counts = []  # TODO Cache them?
        # TODO For performance, create a data structure with only the displayed data?

    # load / refresh / save methods section.

    def load(self):
        # TODO Implement an offline mode.
        self.layoutAboutToBeChanged.emit()
        self._zotero_wrap.initialize()
        self._compute_annotation_counts()
        self.layoutChanged.emit()

    def refresh(self):
        # TODO Implement an offline mode.
        # TODO Only latest sorting kept. Enforce all previous sorting after refresh()?
        self.layoutAboutToBeChanged.emit()
        self._zotero_wrap.load_distant()
        self._compute_annotation_counts()
        self.layoutChanged.emit()

    # Qt interface implementation section.

    def columnCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row = index.row()
        column = index.column()
        if self._is_index_too_large(row, column):
            return None
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return self._cell_data(row, column)
        if role == Qt.BackgroundRole:
            ref_id = self._zotero_wrap.reference_id(row)
            if self.check_id_fct(ref_id) == 2:
                color = QColor(191, 237, 135)
                return QBrush(color, Qt.SolidPattern)
            elif self.check_id_fct(ref_id) == 1:
                color = QColor(150, 150, 150)
                return QBrush(color, Qt.SolidPattern)
            else:
                return None
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        else:
            return super().flags(index) | Qt.ItemIsEditable

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if section >= len(self.HEADERS):
            return None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def insertRow(self, position, ref_type, parent=QModelIndex()):
        """QAbstractItemModel::insertRow() overload to handle reference types.

        The inserted row index will be 'position', which starts at 0.
        """
        self.beginInsertRows(QModelIndex(), position, position)
        reference_template = self._zotero_wrap.create_empty_reference(ref_type)
        self._zotero_wrap.create_local_reference(position, reference_template)
        self.endInsertRows()

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return self._zotero_wrap.reference_count()

    def setData(self, index, value, role=Qt.EditRole):
        # FIXME Use: before, call self.insertRow().
        # FIXME Use: after, call ZoteroWrap.create_distant_reference().
        if not index.isValid():
            return False
        row = index.row()
        column = index.column()
        if self._is_index_too_large(row, column):
            return False
        if role == Qt.EditRole:
            header = self.HEADERS[column]
            if header == "ID":
                self._zotero_wrap.set_reference_id(row, value)
            elif header == "Title":
                self._zotero_wrap.set_reference_title(row, value)
            elif header == "Creators":
                self._zotero_wrap.set_reference_creators(row, value)
            elif header == "Year":
                self._zotero_wrap.set_reference_year(row, value)
            elif header == "Journal":
                self._zotero_wrap.set_reference_journal(row, value)
            elif header == 'Annotations':
                self._set_annotation_count(row, value)
            else:
                return False
            self.dataChanged.emit(index, index)
            return True
        return False

    # Private @properties surrogates section.

    def _annotation_count(self, row):
        """Return the number of annotations of a reference."""
        return self._annotation_counts[row]

    def _set_annotation_count(self, row, value):
        """Set the number of annotations of a reference."""
        self._annotation_counts[row] = value

    # Private methods section.

    def _compute_annotation_counts(self):
        # FIXME Delayed refactoring.
        results = AnnotationSearch(self.annotations_path).search()
        counts = results["Publication ID"].value_counts().to_dict()
        # FIXME Refactoring fix in the meantime.
        self._annotation_counts = [int(counts.get(self._zotero_wrap.reference_id(i), 0))
                                   for i in range(self._zotero_wrap.reference_count())]

    def _is_index_too_large(self, row, column):
        # QModelIndex::isValid() only checks if the index belongs to a model
        # and has non-negative row and column numbers.
        return row >= self.rowCount() or column >= len(self.HEADERS)

    def _cell_data(self, row, column):
        """Return a property of a reference."""
        header = self.HEADERS[column]
        if header == "ID":
            return self._zotero_wrap.reference_id(row)
        elif header == "Title":
            return self._zotero_wrap.reference_title(row)
        elif header == "Creators":
            return self._zotero_wrap.reference_creator_surnames_str(row)
        elif header == "Year":
            # Return int for sorting.
            return self._zotero_wrap.reference_year(row)
        elif header == "Journal":
            return self._zotero_wrap.reference_journal(row)
        elif header == 'Annotations':
            # Return int for sorting.
            return self._annotation_count(row)
