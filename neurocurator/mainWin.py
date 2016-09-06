#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Standard imports
import sys
import os
import webbrowser
import pickle
import getpass
from glob import glob
from os.path import join
from subprocess import call

# Contributed libraries imports
from PySide import QtGui, QtCore
import numpy as np

# NeuroAnnotation Toolbox imports
from nat.utils import Id2FileName #, fileName2Id
from nat.annotation import Annotation
from nat.gitManager import GitManager
from nat.id import checkID
from nat.tag import Tag
from nat.ontoManager import OntoManager
from nat.restClient import RESTClient
    

# Local imports
from .autocomplete import AutoCompleteEdit
from .suggestedTagMng import TagSuggester
#from .qtOntoTrees import TreeModel, TreeView
from .zoteroWrap import ZoteroTableModel
from .uiUtilities import errorMessage, disableTextWidget
from .settingsDlg import getSettings, SettingsDlg
from .annotWidgets import EditAnnotWgt
from .jsonDlg import JSONDlg
from .modParamWidgets import ParamModWgt
from .experimentalPropertyWgt import ExpPropWgt
from .searchInterface import SearchWgt
from .tagWidget import TagWidget
from .annotationListModel import AnnotationListModel
from .searchOntoWgt  import OntoOnlineSearch


class ZoteroUpdateThread(QtCore.QThread):
    def __init__(self, window):
        super(ZoteroUpdateThread, self).__init__()
        self.window = window

    def run(self):

        self.window.statusLabel.setText("Please wait. Loading Zotero database...")
        #statusBar.showMessage("Loading Zotero database...")
        #self.window.splash.showMessage("Loading Zotero database...")
        self.window.zoteroTableModel.refreshDB(self.window.settings.config['ZOTERO']['libraryID'], 
                                                 self.window.settings.config['ZOTERO']['libraryType'], 
                                                 self.window.settings.config['ZOTERO']['apiKey'])

        self.window.zoteroTableModel.sort(self.window.zoteroTableModel.sortCol , 
                                          self.window.zoteroTableModel.sortOrder)
        self.window.zoteroTableModel.refresh()
        #statusBar.clearMessage()
        self.window.statusLabel.setText("Ready.")




class Window(QtGui.QMainWindow):

    selectedAnnotationChangedConfirmed = QtCore.Signal()
    annotationCleared                  = QtCore.Signal()
    savingNeeded                       = QtCore.Signal(bool)

    def popUpSettingsDlg(self):
        self.settings = getSettings(True)
        if self.settings is None:
            self.close()
            self.deleteLater()
            return


    def __init__(self):
        super(Window, self).__init__()

        # Annotation curently being displayed, modified, or created
        self.currentAnnotation = None

        # True when the current annotation has been modified and require saving
        self.needSaving         = False

        self.needSavingDisabled = False

        self._statusBar = self.statusBar()
        self.statusLabel = QtGui.QLabel("")
        self._statusBar.addWidget(self.statusLabel)

        # Get the system username. It will be used to identify the curator
        # in the annotations.
        self.username = getpass.getuser()

        self.loadPersistTag()

        # Number of characters displayed before and after annotations when
        # the annotation is displayed with its context.
        self.contextLength = 30
        
        self.needPush = False

        # True when the annotationEdt field has been modified BY THE USER
        self.detectAnnotChange     = False
    
        # Load the ontological trees (pre-save for efficiency)
        self.builtOntoTrees()

        # Load the tag suggester (based on saved tagging history)
        self.tagSuggester = TagSuggester.load()

        # Load saved settings
        self.settings = getSettings()
        if self.settings is None:
            self.close()
            self.deleteLater()
            return

        # Load the object used to transparently interact with GIT to save annotations
        # using versioning.
        try:
            self.gitMng = GitManager(self.settings.config["GIT"])
        except KeyError:
            self.popUpSettingsDlg()

        # Setup the REST client
        try:
            self.restClient = RESTClient(self.settings.config["REST"]["serverURL"])
        except KeyError:
            self.popUpSettingsDlg()            
            

        # Load from config the path where the GIT database is located.
        self.dbPath   = os.path.abspath(self.settings.config["GIT"]["local"])

        self.setupMenus()
        self.setupWindowsUI()

        self.firstShow = True


    @property
    def needSaving(self):
        return self.__needSaving

    @needSaving.setter
    def needSaving(self, needSaving):
        self.__needSaving = needSaving
        self.savingNeeded.emit(needSaving)



    def loadPersistTag(self):
        if os.path.isfile('persistTag.pkl'):
            try:
                with open('persistTag.pkl', 'rb') as f:
                    self.selectedTagPersist, self.suggestTagPersist  = pickle.load(f)
            except:
                self.selectedTagPersist = {}
                self.suggestTagPersist  = []    
        else:
            self.selectedTagPersist = {}
            self.suggestTagPersist  = []

    def savePersistTag(self):
        with open('persistTag.pkl', 'wb') as f:
            pickle.dump((self.selectedTagPersist, self.suggestTagPersist), f)



    def closeEvent(self, event):
        self.settings.config['WINDOW']['mainSplitterPos']  = str(self.mainWidget.sizes())
        self.settings.config['WINDOW']['leftSplitterPos']  = str(self.leftPanel.sizes())
        self.settings.config['WINDOW']['rightSplitterPos'] = str(self.rightPanel.sizes())
        self.settings.config['WINDOW']['paramModWgtSplitterPos'] = str(self.modParamWgt.rootLayout.sizes())

        colWidths = str([self.zoteroTblWdg.columnWidth(i) for i in range(self.zoteroTableModel.columnCount())])
        self.settings.config['WINDOW']['zotTableViewColWidth'] = colWidths
        self.settings.config['WINDOW']['zotTableSortOrder']      = str(int(self.zoteroTableModel.sortOrder))
        self.settings.config['WINDOW']['zotTableSortCol']          = str(self.zoteroTableModel.sortCol)

        colWidths = str([self.annotListTblWdg.columnWidth(i) for i in range(self.annotTableModel.columnCount())])
        self.settings.config['WINDOW']['annotTableViewColWidth'] = colWidths
        self.settings.config['WINDOW']['annotTableSortOrder']      = str(int(self.annotTableModel.sortOrder))
        self.settings.config['WINDOW']['annotTableSortCol']      = str(self.annotTableModel.sortCol)

        self.settings.save()

        if self.needSaving:
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Unsaved annotation")
            msgBox.setText("The current annotations has been modified. Do you want to save it before quitting?")
            msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
            if msgBox.exec_() == QtGui.QMessageBox.Yes:
                self.saveAnnotation()
            
        if self.needPush:
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("GIT Push recommanded")
            msgBox.setText("Some files have been modified. Do you want to push these modifications to the server before quitting?")
            msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
            if msgBox.exec_() == QtGui.QMessageBox.Yes:
                self.pushToServer()

        event.accept()



    def showEvent(self, event):
        if self.firstShow:
            if 'mainSplitterPos' in self.settings.config['WINDOW']:
                self.mainWidget.setSizes(eval(self.settings.config['WINDOW']['mainSplitterPos']))
            if 'leftSplitterPos' in self.settings.config['WINDOW']:
                self.leftPanel.setSizes(eval(self.settings.config['WINDOW']['leftSplitterPos']))
            if 'rightSplitterPos' in self.settings.config['WINDOW']:
                self.rightPanel.setSizes(eval(self.settings.config['WINDOW']['rightSplitterPos']))
            if 'paramModWgtSplitterPos' in self.settings.config['WINDOW']:
                self.modParamWgt.setRootLayoutSizes(eval(self.settings.config['WINDOW']['paramModWgtSplitterPos']))

            if 'zotTableViewColWidth' in self.settings.config['WINDOW']:            
                for i, width in enumerate(eval(self.settings.config['WINDOW']['zotTableViewColWidth'])):
                    self.zoteroTblWdg.setColumnWidth(i, width)
            if 'annotTableViewColWidth' in self.settings.config['WINDOW']:            
                for i, width in enumerate(eval(self.settings.config['WINDOW']['annotTableViewColWidth'])):
                    self.annotListTblWdg.setColumnWidth(i, width)

            if 'zotTableSortOrder' in self.settings.config['WINDOW']:
                self.zoteroTableModel.sortOrder = QtCore.Qt.SortOrder(int(self.settings.config['WINDOW']['zotTableSortOrder']))

            if 'zotTableSortCol' in self.settings.config['WINDOW']:
                self.zoteroTableModel.sortCol = int(self.settings.config['WINDOW']['zotTableSortCol'])

            if 'annotTableSortOrder' in self.settings.config['WINDOW']:
                self.annotTableModel.sortOrder = QtCore.Qt.SortOrder(int(self.settings.config['WINDOW']['annotTableSortOrder']))

            if 'annotTableSortCol' in self.settings.config['WINDOW']:
                self.annotTableModel.sortCol = int(self.settings.config['WINDOW']['annotTableSortCol'])
            
            self.zoteroTblWdg.sortByColumn(self.zoteroTableModel.sortCol, 
                                        self.zoteroTableModel.sortOrder)

            self.annotListTblWdg.sortByColumn(self.annotTableModel.sortCol, 
                                           self.annotTableModel.sortOrder)



            self.firstShow = False






    def setupMenus(self):
        exitAction = QtGui.QAction(QtGui.QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        openPreferencesAction = QtGui.QAction(QtGui.QIcon(), '&Preferences', self)
        openPreferencesAction.setStatusTip('Edit preferences')
        openPreferencesAction.triggered.connect(self.editPreferences)


        refreshZoteroAction = QtGui.QAction(QtGui.QIcon(), '&Refresh Zotero', self)
        refreshZoteroAction.setStatusTip('Refresh Zotero database')
        refreshZoteroAction.triggered.connect(self.updateZotLib)

        pushToServerAction = QtGui.QAction(QtGui.QIcon(), '&Push to server', self)
        pushToServerAction.setStatusTip('Push modifications to the server')
        pushToServerAction.triggered.connect(self.pushToServer)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)        

        editMenu = menubar.addMenu('&Edit')
        editMenu.addAction(openPreferencesAction)

        commandMenu = menubar.addMenu('&Command')
        commandMenu.addAction(refreshZoteroAction)
        commandMenu.addAction(pushToServerAction)




    def setupWindowsUI(self) :

        self.setupZoteroGB()
        self.setupPaperGB()
        self.setupListAnnotGB()
        self.setupEditAnnotGB()
        self.setupTagAnnotGB()
        self.modParamWgt = ParamModWgt(self)
        self.expPropWgt  = ExpPropWgt(self)

        # Main layout
        self.mainTabs = QtGui.QTabWidget(self)
        self.mainTabs.addTab(self.zoteroGroupBox, "Paper Zotero database")        


        self.taggingTabs = QtGui.QTabWidget(self)
        self.taggingTabs.addTab(self.tagAnnotGroupBox, "Tagging")
        self.taggingTabs.addTab(self.modParamWgt,      "Parameters")
        #self.taggingTabs.addTab(self.expPropWgt,       "Relevant experimental properties")

        self.rightPanel = QtGui.QSplitter(QtCore.Qt.Vertical, self)
        self.rightPanel.setOrientation(QtCore.Qt.Vertical)

        self.leftPanel = QtGui.QSplitter(QtCore.Qt.Vertical, self)
        self.leftPanel.setOrientation(QtCore.Qt.Vertical)

        paperPannel = QtGui.QWidget(self)
        paperPannel.setLayout(QtGui.QVBoxLayout())
        paperPannel.layout().addWidget(self.paperGroupBox)
        paperPannel.layout().addWidget(self.listAnnotGroupBox)

        bottomPannel = QtGui.QWidget(self)
        bottomPannel.setLayout(QtGui.QVBoxLayout())
        bottomPannel.layout().addWidget(self.taggingTabs)



        self.rightPanel.addWidget(bottomPannel)


        self.leftPanel.addWidget(paperPannel)
        self.leftPanel.addWidget(self.editAnnotWgt)
        self.expPropGB = QtGui.QGroupBox("Relevant experimental properties")
        expPropLayout = QtGui.QVBoxLayout(self.expPropGB)
        expPropLayout.addWidget(self.expPropWgt)
        self.leftPanel.addWidget(self.expPropGB)



        self.mainWidget = QtGui.QSplitter(self, QtCore.Qt.Horizontal)
        self.mainWidget.addWidget(self.leftPanel)
        self.mainWidget.addWidget(self.rightPanel)

        self.mainTabs.addTab(self.mainWidget, "Annotations")    

        self.searchTabs =  QtGui.QTabWidget(self)
        self.annotSearchWgt = SearchWgt("Annotation", self)
        self.paramSearchWgt = SearchWgt("Parameter", self)
        
        self.searchTabs.addTab(self.annotSearchWgt, "Annotations")
        self.searchTabs.addTab(self.paramSearchWgt, "Parameters")
        
        self.annotSearchWgt.annotationSelected.connect(self.viewAnnotation)
        self.paramSearchWgt.parameterSelected.connect(self.viewParameter)
        
        self.mainTabs.addTab(self.searchTabs, "Search")    
        
        #self.mainWidget.setSizes([1,1])
        #self.mainWidget.setStretchFactor(0, 1)
        #self.mainWidget.setStretchFactor(1, 1)
        self.setCentralWidget(self.mainTabs)

        # Initial behavior
        self.taggingTabs.setDisabled(True)        





    def setupZoteroGB(self): 
        # Widgets
        self.zoteroTblWdg          = QtGui.QTableView()
        self.zoteroTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.zoteroTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.zoteroTableModel     = ZoteroTableModel(self, self.checkIdInDB)
        self.zoteroTblWdg.setModel(self.zoteroTableModel)
        self.zoteroTableModel.loadCachedDB(self.settings.config['ZOTERO']['libraryID'], 
                                           self.settings.config['ZOTERO']['libraryType'], 
                                           self.settings.config['ZOTERO']['apiKey'])



        self.zoteroTblWdg.doubleClicked.connect(self.changeTagToAnnotations)


        # Layout
        self.zoteroGroupBox     = QtGui.QGroupBox("Zotero database content")
        gridZotero                 = QtGui.QGridLayout(self.zoteroGroupBox)
        gridZotero.addWidget(self.zoteroTblWdg, 0, 0)        
        selection = self.zoteroTblWdg.selectionModel()
        selection.selectionChanged.connect(self.paperSelectionChanged)

        # Initial behavior
        self.zoteroTblWdg.setSortingEnabled(True)
        self.zoteroTblWdg.horizontalHeader().sectionClicked.connect(self.setZotSortCol)



    def changeTagToAnnotations(self):
        self.mainTabs.setCurrentIndex(1)
        

    def setZotSortCol(self, col):
        self.zoteroTableModel.sortCol = col        
        self.zoteroTableModel.sortOrder = self.zoteroTblWdg.horizontalHeader().sortIndicatorOrder()


    def updateZotLib(self):
        self.zoteroThread = ZoteroUpdateThread(self)
        self.zoteroThread.start()

    
    def setupPaperGB(self):
        # Widgets
        self.openPDFBtn                = QtGui.QPushButton('Open PDF', self)
        self.IdTxt                    = QtGui.QLineEdit('', self)

        # Signals
        self.openPDFBtn.clicked.connect(self.openPDF)

        # Layout
        self.paperGroupBox = QtGui.QGroupBox("Paper")
        gridPaper = QtGui.QGridLayout(self.paperGroupBox)
        gridPaper.addWidget(QtGui.QLabel('ID', self), 0, 0)
        gridPaper.addWidget(self.IdTxt, 0, 1)
        gridPaper.addWidget(self.openPDFBtn, 0, 3)
        #gridPaper.addWidget(self.refEdt, 1, 0, 1, 4)

        # Initial behavior
        self.paperGroupBox.setDisabled(True)
        #disableTextWidget(self.refEdt)
        disableTextWidget(self.IdTxt)



    def setupListAnnotGB(self):
        self.cancelledAnnotSelectinChange = False        

        # Widget        
        self.annotListTblWdg      = QtGui.QTableView() 
        self.annotTableModel     = AnnotationListModel(self)
        self.annotListTblWdg.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.annotListTblWdg.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.annotListTblWdg.setModel(self.annotTableModel)

        # Signals
        self.annotationSelectionModel = self.annotListTblWdg.selectionModel()
        self.annotationSelectionModel.selectionChanged.connect(self.selectedAnnotationChanged)
        self.annotTableModel.layoutChanged.connect(self.annotTableLayoutChanged)


        # Layout
        self.listAnnotGroupBox     = QtGui.QGroupBox("Listing of existing annotations")
        gridListAnnotations     = QtGui.QGridLayout(self.listAnnotGroupBox)
        gridListAnnotations.addWidget(self.annotListTblWdg, 0, 0)
        
        # Initial behavior
        self.listAnnotGroupBox.setDisabled(True)        
        self.annotListTblWdg.setSortingEnabled(True)
        self.annotListTblWdg.horizontalHeader().sectionClicked.connect(self.setAnnotSortCol)


    def setAnnotSortCol(self, col):
        self.annotTableModel.sortCol = col        
        self.annotTableModel.sortOrder = self.annotListTblWdg.horizontalHeader().sortIndicatorOrder()


    def setupEditAnnotGB(self):

        self.editAnnotSubWgt = EditAnnotWgt(self)

        self.editAnnotWgt = QtGui.QGroupBox("Annotation details")
        layout               = QtGui.QVBoxLayout(self.editAnnotWgt)
        layout.addWidget(self.editAnnotSubWgt)
        self.editAnnotWgt.setEnabled(False)


    def setupTagAnnotGB(self):
        # Widgets        

        # This fields provide a text fields that can be used
        # to enter tags. It is using an autocompletion scheme which
        # suggests available ontological tags according to entrer word.
        # Matching between entered text and ontological concepts are
        # is not case-sensitive and is not using a prefix scheme (i.e., 
        # matching can be done anywhere within the strings, not only with
        # their begininings)  
        self.tagEdit = AutoCompleteEdit(self)
        self.tagEdit.setMinimumWidth(10)

        self.updateAutoCompleteTagList()

        # List tags that have been selected by the user
        self.selectedTagsWidget = QtGui.QListWidget(self)
        self.selectedTagsWidget.showMaximized()
        self.selectedTagsWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.selectedTagsWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        # List tags that are suggested to the user based on his previous tagging
        # history and on tags that have already been used for other annotations 
        # on this paper.
        self.suggestedTagsWidget = QtGui.QListWidget(self)
        self.suggestedTagsWidget.showMaximized()
        self.suggestedTagsWidget.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.suggestedTagsWidget.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        self.onlineOntoWgt     = OntoOnlineSearch(self)
        self.onlineOntoWgt.tagSelected.connect(self.ontoTagSelected)


        self.tagSelectionTabs = QtGui.QTabWidget(self)
        self.tagSelectionTabs.addTab(self.suggestedTagsWidget, "Suggested tags")     
        self.tagSelectionTabs.addTab(self.onlineOntoWgt, "Search online ontologies")     

    
        # Signals
        self.tagEdit.activated[str].connect(self.tagSuggestionSelected)
        self.tagEdit.editTextChanged.connect(self.editTextChanged)

        # Layout
        self.tagAnnotGroupBox     = QtGui.QGroupBox()
        gridTagAnnotations     = QtGui.QGridLayout(self.tagAnnotGroupBox)
        gridTagAnnotations.addWidget(QtGui.QLabel('Annotation tags', self), 0, 0)
        gridTagAnnotations.addWidget(self.selectedTagsWidget, 1, 0)
        gridTagAnnotations.addWidget(self.tagEdit, 2, 0)
        gridTagAnnotations.addWidget(self.tagSelectionTabs, 0, 1, 3, 1)
        gridTagAnnotations.setColumnStretch(0, 1)
        gridTagAnnotations.setColumnStretch(1, 1)




    def updateAutoCompleteTagList(self):
        # Sort list of suggestions so that more often used tags 
        # are on the top of the autocompletion list
        ids = list(self.tagSuggester.usedTag.keys())
        usage = list(self.tagSuggester.usedTag.values())
        ids.sort(key=dict(zip(ids, usage)).get, reverse=True)

        usedNames = [self.dicData[id] for id in ids if id in self.dicData] 

        allNames  = np.array(list(self.dicData.values()))
  
        # Putting used tag at the top of the list. 
        allNames = np.concatenate([usedNames, allNames[np.logical_not(np.in1d(allNames, usedNames))]])
        
        self.tagEdit.setModel(allNames)
    




    @QtCore.Slot(object, str, str)
    def ontoTagSelected(self, term, curie):
        self.addTagToAnnotation(curie, term)


    @QtCore.Slot(object, object)
    def viewAnnotation(self, annotation):
    
        row = -1
        try:
            for row in range(self.zoteroTableModel.rowCount()):
                if annotation.pubId == self.zoteroTableModel.getID(row):
                    break    
        except:
            print(annotation)
            raise
        assert(row > -1)

        self.zoteroTblWdg.selectRow(row)

        row = -1
        for row, annot in enumerate(self.annotTableModel.annotationList):
            if annot.ID == annotation.ID:
                break
        assert(row > -1)

        self.annotListTblWdg.selectRow(row)
        self.mainTabs.setCurrentIndex(1)

    @QtCore.Slot(object, object, object)
    def viewParameter(self, annotation, parameter):
        self.viewAnnotation(annotation)        
        self.modParamWgt.viewParameter(parameter)
        self.taggingTabs.setCurrentIndex(1)


    def refreshModelingParam(self):
        self.modParamWgt.loadModelingParameter()




    def editPreferences(self):
        settingsDlg = SettingsDlg(self.settings, self)
        if settingsDlg.exec_() == QtGui.QDialog.Accepted:
            self.settings = getSettings()

            self.gitMng = GitManager(self.settings.config["GIT"])
            self.dbPath   = os.path.abspath(self.settings.config["GIT"]["local"])

    def setNeedSaving(self):
        if not self.needSavingDisabled:
            self.needSaving = True


    def annotTableLayoutChanged(self):
        self.selectedAnnotationChanged(self.annotListTblWdg.selectedIndexes())


    def selectedAnnotationChanged(self, selection, deselected=None):

        if not hasattr(self, "editAnnotWgt"):
            # This if is triggered when selectedAnnotationChanged is automatically called
            # in the construction of the dialog. We don't want to run this function in this 
            # context because not all the components of the dialog has been initialized yet.
            return

        ######## This block of code is to manage the cancelation of the change in selected
        ######## annotation when the saving of the previously selected annotation has 
        ######## been unsucessful and the user asked to correct the situation.
        if self.cancelledAnnotSelectinChange :
            self.cancelledAnnotSelectinChange = False
            return False

        if self.checkSavingAnnot() == False:
            if not deselected is None :
                self.cancelledAnnotSelectinChange = True
                self.annotListTblWdg.selectRow(deselected.indexes()[0].row())        
            return False
        ###################


        self.needSavingDisabled = True 
        self.editAnnotWgt.setDisabled(False)
        self.currentAnnotation = self.annotTableModel.getSelectedAnnotation(selection)
        if self.currentAnnotation is None:
            # The current index is invalid. Thus, we deactivate controls
            # used to modify the current annotation.
            self.clearAddAnnotation()
        else:
            self.editAnnotSubWgt.selectAnnotType(self.currentAnnotation.type)

            ## UPDATING EXPERIMENTAL PROPERTIES
            #self.expPropWgt.expPropertiesListModel.clear()
            #for prop in self.currentAnnotation.experimentProperties:
            #    self.expPropWgt.expPropertiesListModel.addProperty(prop.name, prop.value, prop.unit)
            self.expPropWgt.fillingExpPropList()   
            self.expPropWgt.expPropertiesListModel.refresh()


        self.refreshTagList()
        #self.tagAnnotGroupBox.setDisabled(self.currentAnnotation is None)    
        self.taggingTabs.setDisabled(self.currentAnnotation is None)    

        self.detectAnnotChange = False
        self.selectedAnnotationChangedConfirmed.emit()
        self.detectAnnotChange = True
            
        self.refreshModelingParam()
        self.needSavingDisabled = False 



    def builtOntoTrees(self):
        self.ontoMng = OntoManager()
        self.treeData                  = self.ontoMng.trees 
        self.dicData                   = self.ontoMng.dics
        #self.nlTreeModel               = TreeModel(self.treeData)
        #self.nlTreeView                = TreeView(self.nlTreeModel)
        #self.nlTreeView.clicked.connect(self.nlTreeWasClicked)


    #def nlTreeWasClicked(self, selected):
    #    tagId     = selected.data(QtCore.Qt.UserRole)
    #    self.addTagToAnnotation(tagId)


    def getSelectedTags(self):
        return [self.selectedTagsWidget.itemWidget(self.selectedTagsWidget.item(i)).tag for i in range(self.selectedTagsWidget.count())]


    def getSuggestedTags(self):
        return [self.suggestedTagsWidget.itemWidget(self.suggestedTagsWidget.item(i)).tag for i in range(self.suggestedTagsWidget.count())]


    def tagSuggestionSelected(self, name):
        id = [tagId for tagId, tagName in self.dicData.items() if name == tagName]
        assert(len(id)==1)
        id = id[0]
        self.addTagToAnnotation(id)
        self.tagEdit.erase = True
        self.tagEdit.clearEditText()

    def editTextChanged(self, text):
        if self.tagEdit.erase:
            self.tagEdit.clearEditText()
            self.tagEdit.erase = False
            return True
        return False




    def addTagToSelected(self, tagId):
        # check that it is not a duplicate (for the widget)
        if not tagId in [tag.id for tag in self.getSelectedTags()]:
            tag = Tag(tagId, self.dicData[tagId])
            item = QtGui.QListWidgetItem()
            tagEdit = TagWidget(tag, self.selectedTagsWidget)
            self.selectedTagsWidget.addItem(item)
            self.selectedTagsWidget.setItemWidget(item, tagEdit)
            tagEdit.clicked.connect(self.selectedTagClicked)

            # Check if the tag has been persisted for this paper    
            if self.IdTxt.text() in self.selectedTagPersist:
                tagEdit.persist = tagId in self.selectedTagPersist[self.IdTxt.text()]



    def addTagToAnnotation(self, tagId, tagName=None):
        if not tagId in self.currentAnnotation.tagIds:
            if tagName is None:
                tagName = self.dicData[tagId]                
            else:
                if not tagName in self.dicData:
                    self.dicData[tagId] = tagName
                    self.ontoMng.savePickle()
                    self.updateAutoCompleteTagList()

            self.currentAnnotation.addTag(tagId, tagName)
            self.needSaving = True

            self.tagSuggester.addUsedTag(tagId)
            self.refreshTagList()


    def addSuggestedTagFromId(self, tagId):
        tagName = self.dicData[tagId]
        tag = Tag(tagId, tagName)
        item = QtGui.QListWidgetItem()
        tagEdit = TagWidget(tag, self.suggestedTagsWidget)
        self.suggestedTagsWidget.addItem(item)
        self.suggestedTagsWidget.setItemWidget(item, tagEdit)
        tagEdit.clicked.connect(self.suggestedTagClicked)
        tagEdit.persist = tagId in self.suggestTagPersist
    


    def selectedTagClicked(self, tag):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            ID = self.IdTxt.text()
            if not ID in self.selectedTagPersist:
                self.selectedTagPersist[ID] = []
            if tag.id in self.selectedTagPersist[ID]:
                self.selectedTagPersist[ID].remove(tag.id)
            else:
                self.selectedTagPersist[ID].append(tag.id)
        
                # If there is already other annotations associated with this 
                # paper, ask if the persistence should also be applied to them.
                fileName = join(self.dbPath, Id2FileName(self.IdTxt.text())) + ".pcr"
                with open(fileName, "r", encoding="utf-8", errors='ignore') as f:
                    try:
                        annotations = Annotation.readIn(f)
                    except ValueError:
                        raise ValueError("Problem reading file " + fileName + ". The JSON coding of this file seems corrupted.")
            
                isNewAnnot = not self.currentAnnotation in self.annotTableModel.annotationList or self.currentAnnotation is None
                if len(annotations) > 1 - int(isNewAnnot) :
                    msgBox = QtGui.QMessageBox(self)
                    msgBox.setWindowTitle("Tag persistence propagation")
                    msgBox.setText("There is already existing annotations for this paper. Do you want this tag to be added " +
                                   "to them too (any unsaved changes would be saved first)?")
                    msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
                    msgBox.setDefaultButton(QtGui.QMessageBox.No)
                    if msgBox.exec_() == QtGui.QMessageBox.Yes:
                        # Add this tag to existing annotations (associated with the current publication)

                        # Save unsaved modifications if there are any...
                        if self.needSaving:
                            self.saveAnnotation()
                            with open(fileName, "r", encoding="utf-8", errors='ignore') as f:
                                try:
                                    annotations = Annotation.readIn(f)
                                except ValueError:
                                    raise ValueError("Problem reading file " + fileName + ". The JSON coding of this file seems corrupted.")

                        commit = False
                        for annot in annotations:
                            if not tag.id in [annotTag.id for annotTag in annot.tags]:
                                annot.addTag(tag.id, tag.name)
                                commit = True

                        if commit:
                            # TODO: Should be in a try block and if it generate an exception
                            # we should role back to last git version.
                            with open(fileName, "w", encoding="utf-8", errors='ignore') as f:
                                Annotation.dump(f, annotations)

                            self.gitMng.addFiles([fileName])
                            self.refreshListAnnotation()

            self.savePersistTag()
        else:
            self.removeTag(tag)

    def suggestedTagClicked(self, tag):
        modifiers = QtGui.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            if tag.id in self.suggestTagPersist:
                self.suggestTagPersist.remove(tag.id)
            else:
                self.suggestTagPersist.append(tag.id)

            self.savePersistTag()
        else:
            self.removeSuggestedTag(tag)


    def removeTag(self, tag):
        for row, tagItem in enumerate(self.getSelectedTags()):
            if tagItem.id == tag.id:
                self.tagEdit.setFocus()
                self.selectedTagsWidget.takeItem(row)
                self.currentAnnotation.removeTag(tag.id)
                self.needSaving = True
                self.tagSuggester.removeUsedTag(tag.id)
        self.refreshTagList()



    def removeSuggestedTag(self, tag):
        self.addTagToAnnotation(tag.id)


    def openPDF(self):
        pdfFileName = join(self.dbPath, Id2FileName(self.IdTxt.text())) + ".pdf"

        if not os.path.isfile(pdfFileName):
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Missing PDF")
            msgBox.setText("The PDF file seems to be missing. Do you want to attach one?")
            msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
            if msgBox.exec_() == QtGui.QMessageBox.Yes:
                fileName, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file')
                if fileName != '':
                    self.restClient.importPDF(fileName, self.IdTxt.text(), self.dbPath)
                else:
                    return
            else:
                return
                                
        if sys.platform.startswith('darwin'):
            call(('open', pdfFileName))
        elif os.name == 'nt':
            os.startfile(pdfFileName)
        elif os.name == 'posix':
            call(('xdg-open', pdfFileName))


    def checkSavingAnnot(self):
        if self.needSaving:
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Unsaved annotation")
            msgBox.setText("There are unsaved changes in the currently loaded annotation. Do you want to save modifications?")
            msgBox.setStandardButtons(QtGui.QMessageBox.No | QtGui.QMessageBox.Yes)
            msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
            if msgBox.exec_() == QtGui.QMessageBox.Yes:
                self.editAnnotSubWgt.commentEdt.setFocus()
                if self.saveAnnotation() == False:
                    return False
            self.needSaving = False
        return True



    def paperSelectionChanged(self, selected, deselected):
        if self.checkSavingAnnot() == False:
            return False

        row = self.zoteroTblWdg.selectionModel().currentIndex().row()
        DOI = self.zoteroTableModel.getDOI(row)

        # Check if the document as a DOI
        if DOI != "":
            ID = DOI
        else:
            PMID = self.zoteroTableModel.getPMID(row)
            if PMID != "":
                ID = "PMID_" + PMID
            else:
                errorMessage(self, "Error", "This paper has no DOI nor PMID. Processing of papers without DOI nor PMID has not been implemented yet.")
                self.invalidPaperChoice()
                return
                
        self.IdTxt.setText(ID)

        # Check if paper is already in the database
        if not self.checkIdInDB(self.IdTxt.text()):
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Paper not in the database")
            msgBox.setText("This paper is not already in the curator database.")
            pdfButton        = QtGui.QPushButton("Select PDF")
            msgBox.setStandardButtons(QtGui.QMessageBox.Cancel)
            msgBox.addButton(pdfButton, QtGui.QMessageBox.YesRole)

            if DOI != "":
                websiteButton    = QtGui.QPushButton("Follow DOI to the publication website")
                msgBox.addButton(websiteButton, QtGui.QMessageBox.ActionRole)

            msgBox.setDefaultButton(pdfButton)
            retCode = msgBox.exec_() 

            if retCode == 0:
                try:
                    if not self.importPDF():
                        self.invalidPaperChoice()
                        return
                except UnicodeEncodeError:
                    errorMessage(self, "Unicode error", "Please check that the path of the file you are trying to upload does not contain non ASCII characters. Complete support of unicode encoding for file names and paths are not provided.")
                    
            elif retCode == 1 and DOI != "":
                url = "http://dx.doi.org/" + self.IdTxt.text()
                webbrowser.open(url)
                return
            else:
                self.invalidPaperChoice()
                return

        self.refreshListAnnotation(0)
        self.paperGroupBox.setDisabled(False)
        self.listAnnotGroupBox.setDisabled(False)        


    def invalidPaperChoice(self):
        self.clearPaper()
        self.refreshListAnnotation()
        self.clearAddAnnotation()
        self.refreshTagList()
        self.editAnnotWgt.setDisabled(True)
        #self.tagAnnotGroupBox.setDisabled(True)    
        self.taggingTabs.setDisabled(True)    
        self.paperGroupBox.setDisabled(True)        
        self.listAnnotGroupBox.setDisabled(True)            


    def refreshTagList(self):
        self.refreshSelectedTagList()
        self.refreshSuggestedTagList()


    def refreshSelectedTagList(self):
        # Selected tag list
        self.selectedTagsWidget.clear()
        if not self.currentAnnotation is None:
            for id in self.currentAnnotation.tagIds:
                self.addTagToSelected(id)
        self.refreshModelingParam()    



    def refreshSuggestedTagList(self):
        # Suggested tag list
        self.suggestedTagsWidget.clear()
        if not self.currentAnnotation is None:
            annotationFileName = join(self.dbPath, Id2FileName(self.IdTxt.text())) + ".pcr"
            tagIds = self.tagSuggester.suggestions(annotationFileName, [tag.id for tag in self.getSelectedTags()], 200)

            unusedPersistedSuggestedTags = []
            selectedTags                 = [tag.id for tag in self.getSelectedTags()] 
            for persistId in self.suggestTagPersist:
                if persistId in tagIds:
                    tagIds.remove(persistId)
                if not persistId in selectedTags:
                    unusedPersistedSuggestedTags.append(persistId)



            for id in unusedPersistedSuggestedTags + tagIds:    
                self.addSuggestedTagFromId(id)


    def clearPaper(self):
        #self.refEdt.setText("")
        self.IdTxt.setText("")
        


    def importPDF(self):
        # Import a PDF

        if not checkID(self.IdTxt.text()):
            errorMessage(self, "Error", "This ID seem to be invalid.")
            return    


        fileName, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file')
        fileName    = fileName.encode("utf-8").decode("utf-8")
        if fileName != '':
            saveFileName = join(self.dbPath, Id2FileName(self.IdTxt.text()))
            if os.path.isfile(saveFileName + ".txt"):
                errorMessage(self, "Error", "This PDF has already been imported to the database.")

            self.restClient.importPDF(fileName, self.IdTxt.text(), self.dbPath)

            with open(saveFileName + ".pcr", 'w', encoding="utf-8", errors='ignore'): 
                self.gitMng.addFiles([saveFileName + ".pcr"])
                
            return True
        return False



    def pushToServer(self):
        info = self.gitMng.push()
        if info is None:
                        msgBox = QtGui.QMessageBox(self)
                        msgBox.setWindowTitle("Push error")
                        msgBox.setText("The push operation has not been performed because you are in offline mode.")
                        msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
                        msgBox.exec_()

        elif info.flags & info.ERROR :
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Push error")
            msgBox.setText("An error occured while trying to push to the server. Error flag: '" + str(info.flags) + "', message: '" + str(info.summary) + "'.")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgBox.exec_()
        else:
            msgBox = QtGui.QMessageBox(self)
            msgBox.setWindowTitle("Repository pushed to the server")
            msgBox.setText("Modifications has been successfully pushed to the server.")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgBox.exec_()

        self.needPush = False



    def getCurrentContext(self):
        try:
            txtFileName = join(self.dbPath, Id2FileName(self.IdTxt.text())) + ".txt"
            with open(txtFileName, 'r', encoding="utf-8", errors='ignore') as f :
                fileText = f.read()
                contextStart = self.currentAnnotation.start - self.contextLength
                contextEnd = self.currentAnnotation.start + len(self.currentAnnotation.text) + self.contextLength
                return fileText[contextStart:contextEnd]
        except FileNotFoundError:
            return ""



    def deleteAnnotation(self):
        self.annotTableModel.annotationList.remove(self.currentAnnotation)
        self.currentAnnotation = None

        fileName = join(self.dbPath, Id2FileName(self.IdTxt.text())) + ".pcr"
        with open(fileName, "w", encoding="utf-8", errors='ignore') as f:
            Annotation.dump(f, self.annotTableModel.annotationList)

        self.clearAddAnnotation()
        self.gitMng.addFiles([fileName])
        self.needPush = True
        self.needSaving = False
        self.detectAnnotChange = False
        self.refreshListAnnotation()
        self.refreshModelingParam()



    def saveAnnotation(self):

        self.editAnnotSubWgt.updateCurrentAnnotation()
        fileName = join(self.dbPath, Id2FileName(self.IdTxt.text())) + ".pcr"

        with open(fileName, "r", encoding="utf-8", errors='ignore') as f:
            try:
                annots = Annotation.readIn(f)
            except ValueError:
                raise ValueError("Problem reading file " + fileName + ". The JSON coding of this file seems corrupted.")
            
        # Existing annotation has been modified
        if self.currentAnnotation is None:
            return
        if self.currentAnnotation.localizer is None:
            return


        self.currentAnnotation.experimentProperties = self.expPropWgt.getExpProperties()

        if self.currentAnnotation in self.annotTableModel.annotationList:
            for i, annot in enumerate(annots):
                if self.currentAnnotation.ID == annot.ID:
                    annots[i] = self.currentAnnotation
                    break
            row = None


        # New annotation has been created
        else:
            annots.append(self.currentAnnotation)

            # Select the new (last) annotation
            row = -1

        with open(fileName, "w", encoding="utf-8", errors='ignore') as f:
            Annotation.dump(f, annots)

        self.gitMng.addFiles([fileName])
        self.needPush = True
        self.detectAnnotChange = False
        self.needSaving = False
        self.refreshListAnnotation(row)
        return True

        

    def newAnnotation(self):
        if self.checkSavingAnnot() == False:
            return False

        self.clearAddAnnotation()
        self.annotListTblWdg.setCurrentIndex(QtCore.QModelIndex())
        self.currentAnnotation = Annotation(pubId=self.IdTxt.text())
        if self.IdTxt.text() in self.selectedTagPersist:
            for id in self.selectedTagPersist[self.IdTxt.text()]:
                self.currentAnnotation.addTag(id, self.dicData[id])

        self.needSaving = False
        self.refreshTagList()
        self.taggingTabs.setEnabled(True)    
        self.refreshModelingParam()
        return True



    def checkIdInDB(self, ID):
        papersPCR = glob(join(self.dbPath, Id2FileName(ID) + ".pcr")) # paper curation record
        papersPDF = glob(join(self.dbPath, Id2FileName(ID) + ".pdf")) # paper curation record
        papersTXT = glob(join(self.dbPath, Id2FileName(ID) + ".txt")) # paper curation record
        
        if len(papersPCR) == 0:
            return 0 # There is no record yet for this paper.
            
        if len(papersPDF) == 0 or len(papersTXT) == 0:
            return 1 # We have a record, but not pdf or txt.
            
        return 2 # We have a record, a txt and a pdf.

    """
    def Id2FileName(self, ID):
        assert(not forwardSlashEncoder in ID)
        return ID.replace("/", forwardSlashEncoder)

    def fileName2Id(self, fileName):
        assert(not "/" in fileName)
        return fileName.replace(forwardSlashEncoder, "/")
    """

    def clearAddAnnotation(self):
        self.expPropWgt.fillingExpPropList(checkAll=True)
        self.currentAnnotation = None
        tmp = self.detectAnnotChange
        self.detectAnnotChange = False
        self.annotationCleared.emit()
        self.detectAnnotChange = tmp


    def refreshListAnnotation(self, row = None):

        self.annotTableModel.annotationList = []
        try :
            with open(join(self.dbPath, Id2FileName(self.IdTxt.text()) + ".pcr"), 'r', encoding="utf-8", errors='ignore') as f:        
                self.annotTableModel.annotationList = Annotation.readIn(f)    

            if not row is None:
                if row < 0:
                    self.annotListTblWdg.selectRow(self.annotListTblWdg.model().rowCount()-row)
                else:
                    self.annotListTblWdg.selectRow(row)

        except FileNotFoundError:
            # Set and invalid index
            self.annotListTblWdg.selectRow(-1)
        finally:
            self.selectedAnnotationChanged(self.annotListTblWdg.selectedIndexes())

            self.annotListTblWdg.sortByColumn(self.annotTableModel.sortCol, 
                                           self.annotTableModel.sortOrder)

            self.annotTableModel.refresh()




