__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtCore import QModelIndex, Qt, QAbstractTableModel
from PySide.QtGui import QColor, QBrush

from nat.annotationSearch import AnnotationSearch


class ZoteroTableModel(QAbstractTableModel):

    HEADERS = ["ID", "Title", "Creators", "Year", "Journal", "Annotations"]

    def __init__(self, zotero_wrap, check_id_fct, annotations_path, parent=None):
        super().__init__(parent)
        # FIXME Delayed refactoring.
        self.check_id_fct = check_id_fct
        # FIXME Delayed refactoring.
        self.annotations_path = annotations_path
        self._zotero_wrap = zotero_wrap
        # TODO Cache them?
        self._annotation_counts = []
        # TODO For performance, create a data structure with only the displayed data?

    # Data I/O methods section.

    def load(self):
        """Load the Zotero data and compute the annotation counts."""
        self.layoutAboutToBeChanged.emit()
        # TODO Implement an offline mode. Catch PyZoteroError.
        self._zotero_wrap.initialize()
        self._compute_annotation_counts()
        self.layoutChanged.emit()

    def refresh(self):
        """Replace the cached Zotero data with the distant one."""
        # TODO Displayed annotation counts will be inconsistent if new ones
        # have been created during the refresh!
        # TODO Only latest sorting kept. Row numbers change after in the proxy
        # model in this case. Enforce all previous sorting after refresh()?
        self.layoutAboutToBeChanged.emit()
        # TODO Implement an offline mode. Catch PyZoteroError.
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
        if role == Qt.DisplayRole:
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
        elif self.HEADERS[index.column()] == "Annotations":
            return super().flags(index) | Qt.ItemIsEditable
        else:
            return super().flags(index)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if section >= len(self.HEADERS):
            return None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[section]
        return None

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid():
            return 0
        else:
            return self._zotero_wrap.reference_count()

    def setData(self, index, value, role=Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        column = index.column()
        if self._is_index_too_large(row, column):
            return False
        if role == Qt.EditRole:
            if self.HEADERS[column] == 'Annotations':
                self._set_annotation_count(row, value)
                self.dataChanged.emit(index, index)
                return True
        return False

    # Public methods section.

    def add_reference(self, ref):
        """Add the reference at the end. Return the row as a QModelIndex."""
        new_row = self.rowCount()
        self.beginInsertRows(QModelIndex(), new_row, new_row)
        self._zotero_wrap.create_local_reference(ref)
        self._insert_annotation_count()
        self.endInsertRows()
        # NB: Column number will not be used.
        return self.index(new_row, 0, QModelIndex())

    def update_reference(self, row, ref):
        """Update the reference at the given row."""
        self._zotero_wrap.update_local_reference(row, ref)
        start_index = self.index(row, 0, QModelIndex())
        end_index = self.index(row, self.columnCount() - 2, QModelIndex())
        self.dataChanged.emit(start_index, end_index)

    # Private @properties surrogates section.

    def _annotation_count(self, row):
        """Return the number of annotations of the reference at the given row."""
        return self._annotation_counts[row]

    def _set_annotation_count(self, row, count):
        """Set the number of annotations of the reference at the given row."""
        self._annotation_counts[row] = count

    def _insert_annotation_count(self):
        """Insert an annotation count of value 0 at the end, for a new reference."""
        self._annotation_counts.append(0)

    # Private methods section.

    def _compute_annotation_counts(self):
        """Compute the number of annotations for all references and set it."""
        # FIXME Delayed refactoring (related to search).
        results = AnnotationSearch(self.annotations_path).search()
        counts = results["Publication ID"].value_counts().to_dict()
        self._annotation_counts = [int(counts.get(self._zotero_wrap.reference_id(i), 0))
                                   for i in range(self._zotero_wrap.reference_count())]

    def _is_index_too_large(self, row, column):
        """Check if row and column numbers are not out of range.

        QModelIndex::isValid() only checks if the index belongs to a model and
        has non-negative row and column numbers.
        """
        return row >= self.rowCount() or column >= len(self.HEADERS)

    def _cell_data(self, row, column):
        """Return the attribute, in this column, of the reference in this row."""
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
