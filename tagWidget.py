#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

import sys
from PySide import QtGui, QtCore


class Tag:
	def __init__(self, id, name):
		self.id = id
		self.name = name


class TagWidget(QtGui.QLabel):

	clicked = QtCore.Signal(Tag)
		

	def __init__(self, tag, *args, **kwargs):
		self.tag = tag
		super(TagWidget, self).__init__(tag.name, *args, **kwargs)

		self.setAutoFillBackground(True)
		self.persist = False


	def mouseReleaseEvent(self, event):
		modifiers = QtGui.QApplication.keyboardModifiers()
		if modifiers == QtCore.Qt.ShiftModifier:
			self.persist = not self.persist
		self.clicked.emit(self.tag)

	@property
	def persist(self):
		return self.__persist

	@persist.setter
	def persist(self, shouldPersist):
		if shouldPersist:
			ligthRed = QtGui.QColor(255, 153, 153) 
			palette = QtGui.QPalette()
			palette.setColor(self.backgroundRole(),ligthRed)
			self.setPalette(palette)		
		else:
			palette = QtGui.QPalette()
			palette.setColor(self.backgroundRole(),QtCore.Qt.lightGray)
			self.setPalette(palette)
		self.__persist = shouldPersist


