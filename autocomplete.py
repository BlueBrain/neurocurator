from PySide import QtCore, QtGui


class CustomQCompleter(QtGui.QCompleter):
    """
    adapted from: http://stackoverflow.com/a/7767999/2156909
    """
    def __init__(self, *args):#parent=None):
        super(CustomQCompleter, self).__init__(*args)
        self.local_completion_prefix = ""
        self.source_model = None
        self.filterProxyModel = QtGui.QSortFilterProxyModel(self)
        self.usingOriginalModel = False

    def setModel(self, model):
        self.source_model = model
        self.filterProxyModel = QtGui.QSortFilterProxyModel(self)
        self.filterProxyModel.setSourceModel(self.source_model)
        super(CustomQCompleter, self).setModel(self.filterProxyModel)
        self.usingOriginalModel = True

    def updateModel(self):
        if not self.usingOriginalModel:
            self.filterProxyModel.setSourceModel(self.source_model)

        pattern = QtCore.QRegExp(self.local_completion_prefix,
                                QtCore.Qt.CaseInsensitive,
                                QtCore.QRegExp.FixedString)

        self.filterProxyModel.setFilterRegExp(pattern)

    def splitPath(self, path):
        self.local_completion_prefix = path
        self.updateModel()
        if self.filterProxyModel.rowCount() == 0:
            self.usingOriginalModel = False
            self.filterProxyModel.setSourceModel(QtGui.QStringListModel([path]))
            return [path]

        return []

class AutoCompleteEdit(QtGui.QComboBox):
	def __init__(self, *args, **kwargs):
		super(AutoCompleteEdit, self).__init__(*args, **kwargs)

		self.setEditable(True)
		self.setInsertPolicy(self.NoInsert)

		self.comp = CustomQCompleter(self)
		self.comp.setCompletionMode(QtGui.QCompleter.PopupCompletion)
		self.setCompleter(self.comp)
		self.setEditText("")
		self.erase = False

	def setModel(self, strList):
		self.clear()
		self.insertItems(0, strList)
		self.comp.setModel(self.model())

	def focusInEvent(self, event):
		self.clearEditText()
		super(AutoCompleteEdit, self).focusInEvent(event)

	def keyPressEvent(self, event):
		key = event.key()
		if key == 16777220:
		    # Enter (if event.key() == QtCore.Qt.Key_Enter) does not work
		    # for some reason

		    # make sure that the completer does not set the
		    # currentText of the combobox to "" when pressing enter
		    text = self.currentText()
		    self.setCompleter(None)
		    self.setEditText(text)
		    self.setCompleter(self.comp)

		return super(AutoCompleteEdit, self).keyPressEvent(event)

	"""
	def editTextChanged(self, text):
		print("Edit", self.erase)
		if self.erase:
			self.setEditText("")
			self.erase = False
			return True
		else:
			super(AutoCompleteEdit, self).editTextChanged(text)
			return False
	"""
