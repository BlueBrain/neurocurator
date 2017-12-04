#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

from PySide.QtCore import Slot, Qt, QSize
from PySide.QtGui import (QDialog, QComboBox, QFormLayout, QLineEdit,
                          QStackedWidget, QVBoxLayout, QDialogButtonBox,
                          QTableWidget, QWidget, QTableWidgetItem)


class ZoteroReferenceDialog(QDialog):

    def __init__(self, ref_templates, parent=None):
        super().__init__(parent)

        # Own configuration section.

        # TODO Better layout configuration.
        self.setMinimumSize(QSize(800, 1000))

        # Widgets section.

        # TODO Keep only a subset of relevant reference types?
        # TODO Prevent edition of the reference type for an existing reference?
        self._types = list(ref_templates.keys())
        self._types_combo_box = QComboBox()
        self._types_combo_box.addItems(self._types)

        template_widgets = [self._template_widget(x[1]) for x in ref_templates.items()]
        self._template_widgets_stack = QStackedWidget()
        for x in template_widgets:
            self._template_widgets_stack.addWidget(x)

        self._creators_table = CreatorsTableWidget()

        # NB: The first button with the accept role is made the default button.
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # Layouts section.

        header_layout = QFormLayout()
        header_layout.addRow("Reference type:", self._types_combo_box)
        header_layout.addRow("creators: ", self._creators_table)
        header_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        header_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        header_layout.setLabelAlignment(Qt.AlignLeft)
        header_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)

        main_layout = QVBoxLayout()
        main_layout.addLayout(header_layout)
        main_layout.addWidget(self._template_widgets_stack)
        main_layout.addWidget(buttons)
        self.setLayout(main_layout)

        # Signals section.

        self._types_combo_box.currentIndexChanged.connect(self._template_widgets_stack.setCurrentIndex)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    # Load / Refresh / Save methods section.

    def select_reference_type(self, ref_type):
        """Initialize the QDialog for the given reference type."""
        reference_type_index = self._types.index(ref_type)
        self._types_combo_box.setCurrentIndex(reference_type_index)

    def load_reference_data(self, ref_data):
        reference_type = ref_data["itemType"]
        self.select_reference_type(reference_type)
        reference_creators = ref_data["creators"]
        self._creators_table.load_creators(reference_creators)
        self._load_template_fields(ref_data)

    def reference_data(self):
        data = self._template_fields()
        data["itemType"] = self._types_combo_box.currentText()
        headers = self._creators_table.HEADERS
        data["creators"] = [{headers[0]: x[0], headers[1]: x[1], headers[2]: x[2]}
                            for x in self._creators_table.creators()]
        return data

    # Private methods section.

    @staticmethod
    def _template_widget(ref_template):
        widget = QWidget()
        layout = QFormLayout()
        ignored_fields = []
        for field, default_value in ref_template.items():
            if default_value == "":
                # TODO Validate the input (QValidator, inputMask)?
                # TODO Safe edition of the fields in "extra" (line separated).
                layout.addRow(field + ":", QLineEdit())
            elif field not in ["itemType", "creators"]:
                ignored_fields.append(field)
        layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        layout.setLabelAlignment(Qt.AlignLeft)
        layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
        widget.setLayout(layout)
        # TODO Display in the GUI?
        # print("Ignored reference template fields: {}.".format(", ".join(ignored_fields)))
        return widget

    def _template_fields(self):
        fields = {}
        layout = self._template_widgets_stack.currentWidget().layout()
        for i in range(layout.rowCount()):
            field = self._label_text(layout, i)
            # NB: QLineEdit::text() returns an empty string by default.
            value = self._line_edit(layout, i).text()
            fields[field] = value
        return fields

    def _load_template_fields(self, fields):
        layout = self._template_widgets_stack.currentWidget().layout()
        loaded_fields = {"itemType", "creators"}
        for i in range(layout.rowCount()):
            field = self._label_text(layout, i)
            if field in fields:
                line_edit = self._line_edit(layout, i)
                line_edit.setText(fields[field])
                line_edit.home(False)
                loaded_fields.add(field)
        ignored_fields = set(fields.keys()) - loaded_fields
        # TODO Display in the GUI?
        print("Reference fields not loaded for edition (not in the template): "
              "{}.".format(", ".join(ignored_fields)))

    @staticmethod
    def _label_text(form_layout, index):
        return form_layout.itemAt(index, QFormLayout.LabelRole).widget().text().rstrip(":")

    @staticmethod
    def _line_edit(form_layout, index):
        return form_layout.itemAt(index, QFormLayout.FieldRole).widget()


class CreatorsTableWidget(QTableWidget):

    HEADERS = ["firstName", "lastName", "creatorType"]

    def __init__(self, parent=None):
        # NB: "AttributeError: 'columns()' is not a Qt property or a signal"
        # if argument names are used (ie. rows, columns, parent).
        super().__init__(1, 3, parent)

        # Own configuration section.

        self.setHorizontalHeaderLabels(self.HEADERS)
        self.setCornerButtonEnabled(False)
        self.verticalHeader().hide()

        # Signals section.

        # TODO Instead, use a button / double click to add a new row?
        # TODO Validate the input?
        self.cellChanged.connect(self.insert_last_row)

    # Slots section.

    @Slot(int, int)
    def insert_last_row(self, row, column):
        row_count = self.rowCount()
        if row == row_count - 1 and self.item(row, column).text() != "":
            self.insertRow(row_count)

    # Load / Refresh / Save methods section.

    def load_creators(self, creators):
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
        """Return the content in a nested list (1st level: rows, 2nd level: columns)."""
        row_range = range(self.rowCount() - 1)
        column_count = len(self.HEADERS)
        content = [[None] * column_count for i in row_range]
        for i in row_range:
            for j in range(column_count):
                cell = self.item(i, j)
                if cell is not None:
                    content[i][j] = cell.text()
        return content
