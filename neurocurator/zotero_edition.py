#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from collections import OrderedDict
from uuid import uuid4

from PySide.QtCore import Slot, Qt, QSize
from PySide.QtGui import (QDialog, QComboBox, QFormLayout, QLineEdit,
                          QStackedWidget, QDialogButtonBox, QTableWidget,
                          QWidget, QTableWidgetItem, QAbstractItemView,
                          QPushButton, QPlainTextEdit)

from neurocurator import utils


class ZoteroReferenceDialog(QDialog):

    UNPUBLISHED_ID_KEY = "UNPUBLISHED"
    UNPUBLISHED_ID_FIELD = "unpublishedId"
    ITEM_TYPE_FIELD = "itemType"
    CREATORS_FIELD = "creators"
    EXTRA_FIELD = "extra"

    def __init__(self, ref_templates, parent=None):
        super().__init__(parent)

        # Variables sections.

        types_subset = {"book", "bookSection", "conferencePaper", "document",
                        "forumPost", "journalArticle", "patent", "report",
                        "thesis", "webpage"}
        templates_subset = OrderedDict({ref_type: v
                                        for ref_type, v in ref_templates.items()
                                        if ref_type in types_subset})

        self._types = list(templates_subset.keys())

        # Own configuration section.

        # TODO Better layout configuration.
        self.setMinimumSize(QSize(800, 1000))

        # Widgets section.

        # TODO Prevent edition of the reference type for an existing reference?
        self._types_edit = QComboBox()
        self._types_edit.addItems(self._types)

        self._types_widgets = self._templates_widgets(templates_subset)
        types_forms = self._templates_forms(self._types_widgets)
        forms_stack = QStackedWidget()
        for x in types_forms:
            forms_stack.addWidget(x)

        # NB: The first button with the accept role is made the default button.
        ok_cancel = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # Layouts section.

        layout = QFormLayout()
        layout.addRow(self.ITEM_TYPE_FIELD + ":", self._types_edit)
        layout.addRow(forms_stack)
        layout.addRow(ok_cancel)
        # NB: Don't use AllNonFixedFieldsGrow because it expands the QComboBox.
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        utils.configure_form_layout(layout)
        self.setLayout(layout)

        # Signals section.

        self._types_edit.currentIndexChanged.connect(forms_stack.setCurrentIndex)
        ok_cancel.accepted.connect(self.accept)
        ok_cancel.rejected.connect(self.reject)

    # Data I/O methods section.

    def load_reference_data(self, ref_data):
        """Load the reference data into the corresponding edition form."""
        reference_type = ref_data[self.ITEM_TYPE_FIELD]
        self.select_reference_type(reference_type)
        type_widgets = self._types_widgets[reference_type]
        ignored_fields = []
        for field, widget in type_widgets.items():
            if field in ref_data:
                if field == self.CREATORS_FIELD:
                    widget.load_creators(ref_data[self.CREATORS_FIELD])
                elif field == self.EXTRA_FIELD:
                    # NB: '\n' is represented as a new line.
                    widget.setPlainText(ref_data[self.EXTRA_FIELD])
                else:
                    widget.setText(ref_data[field])
                    widget.home(False)
            elif field == self.UNPUBLISHED_ID_FIELD:
                if self.UNPUBLISHED_ID_KEY in ref_data[self.EXTRA_FIELD]:
                    widget.setDisabled(True)
            else:
                ignored_fields.append(field)
        # TODO Display in the GUI?
        if ignored_fields:
            print("Reference fields not loaded for edition: {}.".format(", ".join(ignored_fields)))

    def reference_data(self):
        """Get the reference data from the edition form."""
        reference_type = self._types_edit.currentText()
        type_widgets = self._types_widgets[reference_type]
        data = {self.ITEM_TYPE_FIELD: reference_type}
        for field, widget in type_widgets.items():
            if field == self.CREATORS_FIELD:
                headers = widget.HEADERS
                data[self.CREATORS_FIELD] = [{headers[0]: x[0], headers[1]: x[1], headers[2]: x[2]}
                                             for x in widget.creators()]
            elif field == self.EXTRA_FIELD:
                data[self.EXTRA_FIELD] = widget.toPlainText()
            elif field != self.UNPUBLISHED_ID_FIELD:
                # NB: Return an empty string by default.
                data[field] = widget.text()
        return data

    # Public methods section.

    def select_reference_type(self, ref_type):
        """Select the edition form for the reference type."""
        reference_type_index = self._types.index(ref_type)
        self._types_edit.setCurrentIndex(reference_type_index)

    # Private methods section.

    @staticmethod
    def _templates_forms(templates_widgets):
        """Return the edition forms for the dict {type: {field: widget}}."""
        forms = []
        for type_widgets in templates_widgets.values():
            form = QWidget()
            layout = QFormLayout()
            for field, widget in type_widgets.items():
                layout.addRow(field + ":", widget)
            layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            utils.configure_form_layout(layout)
            form.setLayout(layout)
            forms.append(form)
        return forms

    def _templates_widgets(self, ref_templates):
        """Return the dict {type: {field: widget}} for the reference templates."""
        widgets = OrderedDict()
        special_fields = {self.ITEM_TYPE_FIELD, self.CREATORS_FIELD, self.EXTRA_FIELD}
        for ref_type, template in ref_templates.items():
            text_fields = [field for field, default in template.items()
                           if default == "" and field not in special_fields]
            # TODO Validate the input (QValidator, inputMask)?
            fields = OrderedDict()
            fields[self.CREATORS_FIELD] = CreatorsTableWidget()
            for x in text_fields:
                fields[x] = QLineEdit()
            fields[self.EXTRA_FIELD] = QPlainTextEdit()
            add_unpublished_id = QPushButton("Generate && Add in 'extra'")
            fields[self.UNPUBLISHED_ID_FIELD] = add_unpublished_id
            add_unpublished_id.clicked.connect(self._add_unpublished_id)
            widgets[ref_type] = fields
        return widgets

    def _add_unpublished_id(self):
        """Generate an UUID and add it as the UNPUBLISHED ID in the 'extra' field."""
        reference_type = self._types_edit.currentText()
        type_widgets = self._types_widgets[reference_type]
        type_widgets[self.UNPUBLISHED_ID_FIELD].setDisabled(True)
        # NB: uuid1() may compromise privacy since it creates a UUID containing
        # the computer’s network address. uuid4() creates a random UUID.
        uuid = str(uuid4())
        # NB: If the QPlainTextEdit is not empty, a new line is added before.
        # Otherwise, a new line is not added as first character.
        type_widgets[self.EXTRA_FIELD].appendPlainText("{}: {}".format(self.UNPUBLISHED_ID_KEY, uuid))


class CreatorsTableWidget(QTableWidget):

    HEADERS = ["firstName", "lastName", "creatorType"]

    def __init__(self, parent=None):
        # NB: AttributeError: 'columns()' is not a Qt property or a signal
        # if argument names are used (ie. rows, columns, parent).
        super().__init__(1, 3, parent)

        # Own configuration section.

        self.setCornerButtonEnabled(False)
        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.verticalHeader().hide()
        # NB: Sorting is disabled by default.

        # Signals section.

        # TODO Instead, use a button / double click to add a new row?
        self.cellChanged.connect(self._add_row)

    # Slots section.

    @Slot(int, int)
    def _add_row(self, row, column):
        """Add an empty row at the end if the last row is not empty."""
        row_count = self.rowCount()
        if row == row_count - 1 and self.item(row, column).text() != "":
            self.insertRow(row_count)

    # Data I/O methods section.

    def load_creators(self, creators):
        """Load the creators data into the table."""
        row_count = len(creators)
        column_count = len(self.HEADERS)
        # NB: If sorting enabled, it may interfere with the insertion order.
        for i in range(row_count):
            creator = creators[i]
            self.insertRow(i)
            for j in range(column_count):
                cell_value = creator[self.HEADERS[j]]
                self.setItem(i, j, QTableWidgetItem(cell_value))

    def creators(self):
        """Get the creators data from the table as a nested list [rows: [columns: ]]."""
        row_range = range(self.rowCount() - 1)
        column_count = len(self.HEADERS)
        content = [[None] * column_count for _ in row_range]
        for i in row_range:
            for j in range(column_count):
                cell = self.item(i, j)
                if cell is not None:
                    content[i][j] = cell.text()
        return content
