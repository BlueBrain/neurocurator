#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui, QtCore
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

    restRoot = "https://bbpteam.epfl.ch"

    def __init__(self, settings = None, parent=None):
        super(SettingsDlg, self).__init__(parent)
        self.setWindowTitle("Curator settings")
        self.setGeometry(100, 300, 1000, 200)

        self.settings = settings

        self.projectSettings = ProjectSettings(self.settings)

        self.mainTabs = QtGui.QTabWidget(self)
        self.mainTabs.addTab(self.projectSettings, "Projects")   

        if self.settings is None:
            self.restServerURLTxt = QtGui.QLineEdit(SettingsDlg.restRoot + "/neurocurator/api/v1.0/", self)     
        else:
            self.restServerURLTxt = QtGui.QLineEdit(self.settings.config["REST"]["serverURL"], self) 
            
        self.okBtn            = QtGui.QPushButton('OK', self)


        # Signals
        self.okBtn.clicked.connect(self.writeConfig)

        # Layout
        layout = QtGui.QVBoxLayout()

        # REST server
        self.restGroupBox = QtGui.QGroupBox("REST server")
        grid = QtGui.QGridLayout(self.restGroupBox)
        grid.addWidget(QtGui.QLabel('REST server URL', self), 0, 0)
        grid.addWidget(self.restServerURLTxt, 0, 1)

        layout.addWidget(self.mainTabs)
        layout.addWidget(self.restGroupBox)
        layout.addWidget(self.okBtn)

        self.setLayout(layout)


        # Detect changes in git repository URL
        #self.gitProtocol.currentIndexChanged.connect(self.gitURLChanged)


    def writeConfig(self):
        config = configparser.ConfigParser()

        config['DEFAULT'] = {}

                
        config['REST'] = {'serverURL'      : self.restServerURLTxt.text()}

        if self.settings is None:
            config['WINDOW'] = {}
        elif "WINDOW" in self.settings.config: 
            config['WINDOW'] = self.settings.config["WINDOW"]
        else:
            config['WINDOW'] = {}

        config = self.projectSettings.writeConfig(config)

        with open(os.path.join(os.path.dirname(__file__), 'settings.ini'), 'w') as configfile:
          config.write(configfile)

        self.accept() 






class ProjectSettings(QtGui.QWidget):

    def __init__(self, settings = None, parent=None):
        super(ProjectSettings, self).__init__(parent)

        self.zoteroLibraryTypeCB     = QtGui.QComboBox(self)
        self.zoteroLibraryTypeCB.addItem("group")
        self.zoteroLibraryTypeCB.addItem("user")

        self.settings = settings

        # Creating widgets with initial values
        self.gitProtocol = QtGui.QComboBox(self)
        protocols = ["http", "git+ssh"]
        self.gitProtocol.addItems(protocols)
        self.noRemotechkbox = QtGui.QCheckBox("Don't use any remote", self)
        if self.settings is None:
            self.gitProtocol.setCurrentIndex(0)
            self.gitRemoteTxt     = QtGui.QLineEdit('github.com/christian-oreilly/corpus-thalamus.git', self)
            self.gitLocalTxt      = QtGui.QLineEdit(os.path.expanduser('~/curator_DB/'), self)
            self.gitUserTxt       = QtGui.QLineEdit("git", self) #getpass.getuser(), self)

            self.zoteroLibIDTxt   = QtGui.QLineEdit('427244', self)
            self.zoteroApiKeyTxt  = QtGui.QLineEdit('4D3rDZsAVBd139alqoVZBKOO', self)
            self.zoteroLibraryTypeCB.setCurrentIndex(0)

            self.restServerURLTxt = QtGui.QLineEdit(SettingsDlg.restRoot + "neurocurator/api/v1.0/", self) 
            
            self.noRemotechkbox.setCheckState(QtCore.Qt.Unchecked)
    
        else:
                
            if self.settings.config['GIT']['remote'] == "":
                self.gitRemoteTxt     = QtGui.QLineEdit("", self)
                self.gitUserTxt       = QtGui.QLineEdit("", self)
                self.noRemotechkbox.setCheckState(QtCore.Qt.Checked)
          
            else:
                self.gitRemoteTxt     = QtGui.QLineEdit(self.settings.config['GIT']['remote'], self)
                self.gitUserTxt       = QtGui.QLineEdit(self.settings.config['GIT']['user'], self)
                self.noRemotechkbox.setCheckState(QtCore.Qt.Unchecked)
                
                if "protocol" in self.settings.config['GIT']:
                    self.gitProtocol.setCurrentIndex(protocols.index(self.settings.config['GIT']['protocol']))
                else:
                    self.gitProtocol.setCurrentIndex(0)          
          
            self.gitLocalTxt      = QtGui.QLineEdit(self.settings.config['GIT']['local'], self)

            self.zoteroLibIDTxt   = QtGui.QLineEdit(self.settings.config['ZOTERO']['libraryID'], self)
            self.zoteroApiKeyTxt  = QtGui.QLineEdit(self.settings.config['ZOTERO']['apiKey'], self)
            if self.settings.config['ZOTERO']['libraryType'] == "group":
                self.zoteroLibraryTypeCB.setCurrentIndex(0)
            elif self.settings.config['ZOTERO']['libraryType'] == "user":
                self.zoteroLibraryTypeCB.setCurrentIndex(1)
            else:
                raise ValueError
                
                
        self.zoteroLibraryIDInstructions = QtGui.QLabel('', self)
        self.zoteroLibraryIDInstructions.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse)
        self.zoteroLibraryIDInstructions.setOpenExternalLinks(True)

        # Signals
        self.zoteroLibraryTypeCB.currentIndexChanged.connect(self.updateZoteroLibraryIDInstructions)
        self.noRemotechkbox.stateChanged.connect(self.noRemoteChanged)

        # Layout
        layout = QtGui.QVBoxLayout()

        # GIT
        self.gitGroupBox = QtGui.QGroupBox("GIT")
        gridGIT = QtGui.QGridLayout(self.gitGroupBox)
        
        gridGIT.addWidget(QtGui.QLabel('Remote repository', self), 0, 0)
        gridGIT.addWidget(self.gitProtocol, 0, 1)
        gridGIT.addWidget(QtGui.QLabel('://', self), 0, 2)
        gridGIT.addWidget(self.gitUserTxt, 0, 3)
        gridGIT.addWidget(QtGui.QLabel('@', self), 0, 4)
        gridGIT.addWidget(self.gitRemoteTxt, 0, 5)
        
        gridGIT.addWidget(self.noRemotechkbox, 1, 0, 1, 6)
                
        gridGIT.addWidget(QtGui.QLabel('Local repository', self), 2, 0)
        gridGIT.addWidget(self.gitLocalTxt, 2, 1, 1, 5)

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
        privateKeyInst = QtGui.QLabel("You're private key can be generate here: <a href=\"https://www.zotero.org/settings/keys/new\">https://www.zotero.org/settings/keys/new</a>", self)
        privateKeyInst.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse)
        privateKeyInst.setOpenExternalLinks(True)
        gridGIT.addWidget(privateKeyInst, 4, 1, 1, 2)

        
        self.updateZoteroLibraryIDInstructions()


        layout.addWidget(self.gitGroupBox)
        layout.addWidget(self.zoteroGroupBox)

        self.setLayout(layout)


        # Detect changes in git repository URL
        #self.gitProtocol.currentIndexChanged.connect(self.gitURLChanged)

    def noRemoteChanged(self, checked):
        self.gitProtocol.setDisabled(self.noRemotechkbox.checkState())
        self.gitUserTxt.setDisabled(self.noRemotechkbox.checkState())
        self.gitRemoteTxt.setDisabled(self.noRemotechkbox.checkState())



    def updateZoteroLibraryIDInstructions(self):
        if self.zoteroLibraryTypeCB.currentText() == "group":
            self.zoteroLibraryIDInstructions.setText('The ID can be found by opening the group’s page (links to your groups page should be ' +
                                                     '<a href=\"https://www.zotero.org/groups/\">here</a>), and hovering\n' +
                                                     'over the group settings link. The ID is the integer after ' +
                                                     '/groups/. You must be the owner of the group to see the setting link.')
        elif self.zoteroLibraryTypeCB.currentText() == "user":
            self.zoteroLibraryIDInstructions.setText('Personal libary ID can be found here: ' + 
                                                     '<a href=\"https://www.zotero.org/settings/keys\">https://www.zotero.org/settings/keys</a>')
        else:
            raise ValueError


    def writeConfig(self, config):

        config['GIT'] = {'protocol'        : self.gitProtocol.currentText(),
                         'remote'          : self.gitRemoteTxt.text(),
                         'local'           : self.gitLocalTxt.text(),
                         'user'            : self.gitUserTxt.text()}

        config['ZOTERO'] = {'libraryID'    : self.zoteroLibIDTxt.text(),
                            'apiKey'       : self.zoteroApiKeyTxt.text(),
                            'libraryType'  : self.zoteroLibraryTypeCB.currentText()}
                
        return config
