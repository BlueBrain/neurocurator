#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui, QtCore



"""
class MyDelegate(QtGui.QStyledItemDelegate):
	def __init__(self, parent=None):
		super(MyDelegate, self).__init__(parent)


	def paint(self, painter, option, index):
		if option.state & QtGui.QStyle.State_Selected :
			painter.fillRect(option.rect, option.palette.color(QtGui.QPalette.Highlight))

		title = index.data(QtCore.Qt.DisplayRole)
		description = index.data(QtCore.Qt.UserRole + 1)

		r = option.rect.adjusted(50, 0, 0, -50)
		painter.drawText(r, QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft | QtCore.Qt.TextWordWrap, title)

		r = option.rect.adjusted(50, 50, 0, 0)
		painter.drawText(r, QtCore.Qt.AlignLeft | QtCore.Qt.TextWordWrap, description)


	def sizeHint(self, option, index):
		return QtCore.QSize(200, 100)

"""


class TextEdit(QtGui.QTextEdit):
	
	def __init__(self, no, *args, **kwargs):
		self.no = no
		super(TextEdit, self).__init__(*args, **kwargs)

	clicked = QtCore.Signal(int)
	def mouseReleaseEvent(self, event):
		self.clicked.emit(self.no)

class MatchDlg(QtGui.QDialog):

	def __init__(self, blocks, text, fileText, parent=None):
		super(MatchDlg, self).__init__(parent)
		self.setWindowTitle("Approximate matches")
		self.setGeometry(100, 300, 1000, 200)

		NContext = 30

		self.listWidget = QtGui.QListWidget(self)

		for row, block in enumerate(blocks):
			item = QtGui.QListWidgetItem()

			before = fileText[block["start"]-NContext:block["start"]]
			after = fileText[block["end"]:block["end"]+NContext]

			item.setSizeHint(QtCore.QSize(1000, 50))
			textEdit = TextEdit(row, self)
			textEdit.insertHtml('{}<b>{}</b>{}'.format(before, block["candidate"], after))
			self.listWidget.addItem(item)
			self.listWidget.setItemWidget(item, textEdit)


			textEdit.clicked.connect(self.selectText)


		self.listWidget.showMaximized()

		self.listWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.listWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

		self.selection = self.listWidget.selectionModel()
		self.selection.selectionChanged.connect(self.selectText)
		

		layout = QtGui.QVBoxLayout()
		layout.addWidget(QtGui.QLabel('The text to annotate has not been found. Similar entries are listed below. Please choose correct one.', self))
		layout.addWidget(self.listWidget)
		self.setLayout(layout)

		self.blocks = blocks
		self.chosenBlock = None


	def selectText(self, row):
		self.chosenBlock = self.blocks[row]
		self.accept()

