from PySide import QtCore, QtGui
from copy import deepcopy
from sys import platform as _platform

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

	def setModel(self, strList): 
		self.source_model =  QtGui.QStringListModel(strList)
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

		self.usingOriginalModel = True
		return []

class AutoCompleteEdit(QtGui.QComboBox):

	enterKeyPressed = QtCore.Signal(QtGui.QComboBox)

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
		self.comp.setModel(strList)

	def focusInEvent(self, event):
		if _platform == "linux" or _platform == "linux2":
  			# This behavior is the original one, which is fine in linux. On MacOS,
			# selecting an item change the value of the combobox and then set the focus on it
			# which was making this line erase the selected text.
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
			self.enterKeyPressed.emit(self)


			# TODO: Implement cancellation on ESC key

		return super(AutoCompleteEdit, self).keyPressEvent(event)



