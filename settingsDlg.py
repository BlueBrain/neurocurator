#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui, QtCore
import configparser
import getpass

def getSettings():
	try:
		return Settings()
	except FileNotFoundError:
		form = SettingsDlg()
		if form.exec_() == QtGui.QDialog.Accepted:
			return getSettings()
		else:
			return None

class Settings:
	def __init__(self):
		self.config = configparser.ConfigParser()
		open('settings.ini') # Raise an exception if file does not exist
		self.config.read('settings.ini')

	def save(self):
		with open('settings.ini', 'w') as configfile:
		  self.config.write(configfile)


class SettingsDlg(QtGui.QDialog):

	def __init__(self, settings = None, parent=None):
		super(SettingsDlg, self).__init__(parent)
		self.setWindowTitle("Curator settings")
		self.setGeometry(100, 300, 1000, 200)

		self.zoteroLibraryTypeCB 	= QtGui.QComboBox(self)
		self.zoteroLibraryTypeCB.addItem("group")
		self.zoteroLibraryTypeCB.addItem("user")

		self.settings = settings

		# Creating widgets with initial values
		if self.settings is None:
			self.gitRemoteTxt 	= QtGui.QLineEdit('bbpcode.epfl.ch/project/proj55/curator_DB', self)
			self.gitLocalTxt 	= QtGui.QLineEdit('curator_DB', self)
			self.gitUserTxt 	= QtGui.QLineEdit(getpass.getuser(), self)

			self.zoteroLibIDTxt 	= QtGui.QLineEdit('427244', self)
			self.zoteroApiKeyTxt 	= QtGui.QLineEdit('4D3rDZsAVBd139alqoVZBKOO', self)
			self.zoteroLibraryTypeCB.setCurrentIndex(0)
	
		else:
			self.gitRemoteTxt 		= QtGui.QLineEdit(self.settings.config['GIT']['remote'], self)
			self.gitLocalTxt 		= QtGui.QLineEdit(self.settings.config['GIT']['local'], self)
			self.gitUserTxt 		= QtGui.QLineEdit(self.settings.config['GIT']['user'], self)

			self.zoteroLibIDTxt 	= QtGui.QLineEdit(self.settings.config['ZOTERO']['libraryID'], self)
			self.zoteroApiKeyTxt 	= QtGui.QLineEdit(self.settings.config['ZOTERO']['apiKey'], self)
			if self.settings.config['ZOTERO']['libraryType'] == "group":
				self.zoteroLibraryTypeCB.setCurrentIndex(0)
			elif self.settings.config['ZOTERO']['libraryType'] == "user":
				self.zoteroLibraryTypeCB.setCurrentIndex(1)
			else:
				raise ValueError

		self.okBtn			= QtGui.QPushButton('OK', self)

		self.zoteroLibraryIDInstructions = QtGui.QLabel('', self)


		# Signals
		self.okBtn.clicked.connect(self.writeConfig)
		self.zoteroLibraryTypeCB.currentIndexChanged.connect(self.updateZoteroLibraryIDInstructions)

		# Layout
		layout = QtGui.QVBoxLayout()

		# GIT
		self.gitGroupBox = QtGui.QGroupBox("GIT")
		gridGIT = QtGui.QGridLayout(self.gitGroupBox)
		gridGIT.addWidget(QtGui.QLabel('Remove repository', self), 0, 0)
		gridGIT.addWidget(QtGui.QLabel('ssh://', self), 0, 1)
		gridGIT.addWidget(self.gitUserTxt, 0, 2)
		gridGIT.addWidget(QtGui.QLabel('@', self), 0, 3)
		gridGIT.addWidget(self.gitRemoteTxt, 0, 4)
		gridGIT.addWidget(QtGui.QLabel('Local repository', self), 1, 0)
		gridGIT.addWidget(self.gitLocalTxt, 1, 1, 1, 4)

		# Zotero
		self.zoteroGroupBox = QtGui.QGroupBox("Zotero")
		gridGIT = QtGui.QGridLayout(self.zoteroGroupBox)
		gridGIT.addWidget(QtGui.QLabel('Library type', self), 0, 0)
		gridGIT.addWidget(self.zoteroLibraryTypeCB, 0, 1)
		gridGIT.addWidget(QtGui.QLabel('Library ID', self), 1, 0)
		gridGIT.addWidget(self.zoteroLibIDTxt, 1, 1)
		gridGIT.addWidget(self.zoteroLibraryIDInstructions, 2, 1, 1, 2)
		gridGIT.addWidget(QtGui.QLabel('API Key', self), 3, 0)
		gridGIT.addWidget(self.zoteroApiKeyTxt, 3, 1)
		gridGIT.addWidget(QtGui.QLabel("You're private key can be generate here: https://www.zotero.org/settings/keys/new", self), 4, 1, 1, 2)
		self.updateZoteroLibraryIDInstructions()

		layout.addWidget(self.gitGroupBox)
		layout.addWidget(self.zoteroGroupBox)
		layout.addWidget(self.okBtn)

		self.setLayout(layout)

	def updateZoteroLibraryIDInstructions(self):
		if self.zoteroLibraryTypeCB.currentText() == "group":
			self.zoteroLibraryIDInstructions.setText('The ID can be found by opening the group’s page: ' +
													 'https://www.zotero.org/groups/groupname, and hovering\n' +
													 'over the group settings link. The ID is the integer after ' +
													 '/groups/. You must be the owner of the group to see the setting link.')
		elif self.zoteroLibraryTypeCB.currentText() == "user":
			self.zoteroLibraryIDInstructions.setText('Personal libary ID can be found here: https://www.zotero.org/settings/keys')
		else:
			raise ValueError


	def writeConfig(self):
		config = configparser.ConfigParser()

		config['DEFAULT'] = {}

		config['GIT'] = {'remote'	: self.gitRemoteTxt.text(),
				         'local'	: self.gitLocalTxt.text(),
				         'user' 	: self.gitUserTxt.text()}

		config['ZOTERO'] = {'libraryID'		: self.zoteroLibIDTxt.text(),
				            'apiKey'		: self.zoteroApiKeyTxt.text(),
				            'libraryType' 	: self.zoteroLibraryTypeCB.currentText()}

		if self.settings is None:
			config['WINDOW'] = {}
		elif "WINDOW" in self.settings.config: 
			config['WINDOW'] = self.settings.config["WINDOW"]
		else:
			config['WINDOW'] = {}

		with open('settings.ini', 'w') as configfile:
		  config.write(configfile)

		self.accept() 

