# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:49:40 2016

@author: oreilly
"""

#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui
from uuid import uuid1
from nat.zoteroWrap import ZoteroWrap





class AddToZoteroDlg(QtGui.QDialog):

    def __init__(self, zotWrapTable, parent=None):
        super(AddToZoteroDlg, self).__init__(parent)
        
        self.setWindowTitle("Addition of a Zotero reference")
        self.setGeometry(100, 300, 1000, 1000)

        self.zotWrapTable = zotWrapTable

        self.docType = QtGui.QComboBox(self)
        self.itemTypes = self.zotWrapTable.itemTypes
        self.docType.addItems([t["localized"] for t in self.itemTypes])    
        self.documentObjects = [DocumentObject(t, self.zotWrapTable) for t in self.itemTypes]
                    
        layout = QtGui.QGridLayout()
        layout.addWidget(QtGui.QLabel("Document type: ", self), 0, 0)
        layout.addWidget(self.docType , 0, 1)

        self.stackedWidget =  QtGui.QStackedWidget()
        for docObj in self.documentObjects:
            self.stackedWidget.addWidget(docObj.getGroup())

        self.docType.activated.connect(self.stackedWidget.setCurrentIndex)
        layout.addWidget(self.stackedWidget , 1, 0, 1, 2)
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | 
                                                QtGui.QDialogButtonBox.Cancel)
        
        self.buttonBox.accepted.connect(self.addReference)
        self.buttonBox.rejected.connect(self.reject)        

        layout.addWidget(self.buttonBox , 2, 1)

        self.setLayout(layout)
      
         
    def addReference(self):
        reference = self.documentObjects[self.docType.currentIndex()].getReference() 
        resp = self.zotWrapTable.zotLib.create_items([reference])
        if len(resp["success"]) != 1:
            raise ValueError("Error while trying to add a Zotero record : " + str(resp))

        self.zotWrapTable.addItem(reference)
        self.accept()
         




class CreatorsWgt(QtGui.QTableWidget):
    
    def __init__(self, creatorsLst):
        super(CreatorsWgt, self).__init__()
        self.setColumnCount(2);
        self.setHorizontalHeaderLabels(["First name", "Last name"])         
        self.creatorsLst = creatorsLst
        
        self.setColumnWidth(0, self.width()/2);
        self.setColumnWidth(1, self.width()/2);       
        self.insertRow(0)

        self.cellChanged.connect(self.checkAddRow)

    def checkAddRow(self, row, column):
        if row == self.rowCount()-1:
            self.insertRow(self.rowCount())


        
    def getCreatorsLst(self):
        creatorType = self.creatorsLst[0]["creatorType"] 
        
        outList = []
        for i in range(self.rowCount()):
            if not self.item(i, 0) is None and not self.item(i, 1) is None:
                if self.item(i, 0).text() != "" or self.item(i, 1).text() != "" :
                    creatorDict = {'creatorType':creatorType,
                                   'firstName': self.item(i, 0).text(), 
                                   'lastName': self.item(i, 1).text()}
                    outList.append(creatorDict)           
                
        return outList



class IdWgt(QtGui.QWidget):
    
    def __init__(self):
        super(IdWgt, self).__init__()        
        self.idType = QtGui.QComboBox(self)
        self.idType.addItems(["DOI", "PMID", "UNPUBLISHED"])
        self.stackedWidget =  QtGui.QStackedWidget()      
        self.idType.activated.connect(self.stackedWidget.setCurrentIndex)
        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.idType)
        layout.addWidget(self.stackedWidget)

        self.stackedWidget.addWidget(QtGui.QLineEdit())
        self.stackedWidget.addWidget(QtGui.QLineEdit())
        self.stackedWidget.addWidget(QtGui.QLineEdit(str(uuid1())))

        self.stackedWidget.widget(2).setDisabled(True)

    
    def setIdToReference(self, reference):
        
        if self.idType.currentText() == "DOI":
            reference["DOI"] = self.stackedWidget.currentWidget().text()
        elif self.idType.currentText() == "PMID":
            reference["extra"] += "/nPMID:" + self.stackedWidget.currentWidget().text()
        elif self.idType.currentText() == "UNPUBLISHED":
            reference["extra"] += "/nUNPUBLISHED:" + self.stackedWidget.currentWidget().text()

        return reference





class DocumentObject:        

    def __init__(self, docItemType, zotWrap):
        self.zotLib = zotWrap.zotLib
        self.reference = zotWrap.itemTemplates[docItemType["itemType"]]

    def getCreatorsWidget(self, creatorsLst):
        return CreatorsWgt(creatorsLst)
        

    def getIdWidget(self):
        return IdWgt()
        

    def getReference(self):
        
        for key, widget in self.widgets.items():
            if key == "Id":
                self.reference = widget.setIdToReference(self.reference)
            else:
                if isinstance(self.reference[key], str):
                    if key != "DOI":
                        self.reference[key] = str(widget.text())
                elif isinstance(self.reference[key], (dict, list)):
                    if key == "creators":    
                        self.reference[key] = widget.getCreatorsLst()
        
        # check_item is broken: see https://github.com/urschrei/pyzotero/issues/69
        #return self.zotLib.check_items([self.reference])[0]
        return self.reference


        
    def getGroup(self):

        group = QtGui.QWidget()
        
        layout = QtGui.QGridLayout(group)
        self.widgets = {}

        no = 0 # Not using the loop enumerate because we may want to skip some items
        for key, value in self.reference.items():
            if isinstance(value, str):
                if key == "itemType":
                    continue                    
                self.widgets[key] = QtGui.QLineEdit()  
            elif isinstance(value, (dict, list)):            
                if key == "creators":
                    self.widgets[key] = self.getCreatorsWidget(value)
                else:
                    continue
            else:
                continue
                        
            layout.addWidget(QtGui.QLabel(key + ": "), no, 0)                
            layout.addWidget(self.widgets[key] , no, 1)
            no += 1

        self.widgets["Id"] = self.getIdWidget()
        
        layout.addWidget(self.widgets["Id"] , no, 0, 1, 2)

        return group    
