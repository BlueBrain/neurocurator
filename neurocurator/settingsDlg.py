#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui
import configparser
import os
#import getpass

def getSettings(popDialog = False):
    
    def popDialogFct():
        form = SettingsDlg()
        if form.exec_() == QtGui.QDialog.Accepted:
            return getSettings()
        else:
            return None
    
    if popDialog:
        return popDialogFct()             
    
    try:
        return Settings()
    except FileNotFoundError:
        return popDialogFct()        
        

class Settings:
    fileName = os.path.join(os.path.dirname(__file__), 'settings.ini')
    def __init__(self):
        self.config = configparser.ConfigParser()
        with open(Settings.fileName) as configfile: # Raise an exception if file does not exist
            self.config.read(Settings.fileName)
            #self.config.read(configfile)

    def save(self):
        with open(Settings.fileName, 'w') as configfile:
          self.config.write(configfile)


class SettingsDlg(QtGui.QDialog):

    def __init__(self, settings = None, parent=None):
        super(SettingsDlg, self).__init__(parent)
        self.setWindowTitle("Curator settings")
        self.setGeometry(100, 300, 1000, 200)

        self.zoteroLibraryTypeCB     = QtGui.QComboBox(self)
        self.zoteroLibraryTypeCB.addItem("group")
        self.zoteroLibraryTypeCB.addItem("user")

        self.settings = settings

        # Creating widgets with initial values
        self.gitProtocol = QtGui.QComboBox(self)
        protocols = ["http", "git+ssh"]
        self.gitProtocol.addItems(protocols)
        if self.settings is None:
            self.gitProtocol.setCurrentIndex(0)
            self.gitRemoteTxt     = QtGui.QLineEdit('github.com/christian-oreilly/corpus-thalamus.git', self)
            self.gitLocalTxt      = QtGui.QLineEdit(os.path.expanduser('~/curator_DB/'), self)
            self.gitUserTxt       = QtGui.QLineEdit("git", self) #getpass.getuser(), self)

            self.zoteroLibIDTxt   = QtGui.QLineEdit('427244', self)
            self.zoteroApiKeyTxt  = QtGui.QLineEdit('4D3rDZsAVBd139alqoVZBKOO', self)
            self.zoteroLibraryTypeCB.setCurrentIndex(0)

            self.restServerURLTxt = QtGui.QLineEdit("http://bbpca063.epfl.ch:5000/neurocurator/api/v1.0/", self) 
    
        else:
            if "protocol" in self.settings.config['GIT']:
                self.gitProtocol.setCurrentIndex(protocols.index(self.settings.config['GIT']['protocol']))
            else:
                self.gitProtocol.setCurrentIndex(0)
                
            self.gitRemoteTxt     = QtGui.QLineEdit(self.settings.config['GIT']['remote'], self)
            self.gitLocalTxt      = QtGui.QLineEdit(self.settings.config['GIT']['local'], self)
            self.gitUserTxt       = QtGui.QLineEdit(self.settings.config['GIT']['user'], self)

            self.zoteroLibIDTxt   = QtGui.QLineEdit(self.settings.config['ZOTERO']['libraryID'], self)
            self.zoteroApiKeyTxt  = QtGui.QLineEdit(self.settings.config['ZOTERO']['apiKey'], self)
            if self.settings.config['ZOTERO']['libraryType'] == "group":
                self.zoteroLibraryTypeCB.setCurrentIndex(0)
            elif self.settings.config['ZOTERO']['libraryType'] == "user":
                self.zoteroLibraryTypeCB.setCurrentIndex(1)
            else:
                raise ValueError

            self.restServerURLTxt = QtGui.QLineEdit(self.settings.config["REST"]["serverURL"], self) 
            

        self.okBtn            = QtGui.QPushButton('OK', self)

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
        gridGIT.addWidget(self.gitProtocol, 0, 1)
        gridGIT.addWidget(QtGui.QLabel('://', self), 0, 2)
        gridGIT.addWidget(self.gitUserTxt, 0, 3)
        gridGIT.addWidget(QtGui.QLabel('@', self), 0, 4)
        gridGIT.addWidget(self.gitRemoteTxt, 0, 5)
        gridGIT.addWidget(QtGui.QLabel('Local repository', self), 1, 0)
        gridGIT.addWidget(self.gitLocalTxt, 1, 1, 1, 5)

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

        # REST server
        self.restGroupBox = QtGui.QGroupBox("REST server")
        gridGIT = QtGui.QGridLayout(self.restGroupBox)
        gridGIT.addWidget(QtGui.QLabel('REST server URL', self), 0, 0)
        gridGIT.addWidget(self.restServerURLTxt, 0, 1)

        layout.addWidget(self.gitGroupBox)
        layout.addWidget(self.zoteroGroupBox)
        layout.addWidget(self.restGroupBox)
        layout.addWidget(self.okBtn)

        self.setLayout(layout)


        # Detect changes in git repository URL
        #self.gitProtocol.currentIndexChanged.connect(self.gitURLChanged)





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

        config['GIT'] = {'protocol'        : self.gitProtocol.currentText(),
                         'remote'          : self.gitRemoteTxt.text(),
                         'local'           : self.gitLocalTxt.text(),
                         'user'            : self.gitUserTxt.text()}

        config['ZOTERO'] = {'libraryID'    : self.zoteroLibIDTxt.text(),
                            'apiKey'       : self.zoteroApiKeyTxt.text(),
                            'libraryType'  : self.zoteroLibraryTypeCB.currentText()}
                
        config['REST'] = {'serverURL'      : self.restServerURLTxt.text()}

        if self.settings is None:
            config['WINDOW'] = {}
        elif "WINDOW" in self.settings.config: 
            config['WINDOW'] = self.settings.config["WINDOW"]
        else:
            config['WINDOW'] = {}

        with open(os.path.join(os.path.dirname(__file__), 'settings.ini'), 'w') as configfile:
          config.write(configfile)

        self.accept() 

