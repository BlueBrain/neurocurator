# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:49:40 2016

@author: oreilly
"""

#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui, QtCore
from uuid import uuid1
from copy import deepcopy
from warnings import warn


class AddToZoteroDlg(QtGui.QDialog):

    def __init__(self, zotWrapTable, row=None, parent=None):
        """
         If row is None, this methods create a new item in the Zotero colleciton.
         If row is not None, it loads the item corresponding to this row and
         apply any modification to this item.
        """
        super(AddToZoteroDlg, self).__init__(parent)
        
        self.setWindowTitle("Addition of a Zotero reference")
        self.setGeometry(100, 300, 1000, 1000)

        self.zotWrapTable = zotWrapTable

        self.docType = QtGui.QComboBox(self)
        self.itemTypes = self.zotWrapTable.itemTypes
        self.docType.addItems([t["itemType"] for t in self.itemTypes])  # localized  
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
      
        if not row is None:
            self.updateExisting = True
            self.loadReference(row)            
        else:
            self.updateExisting = False

      
      
    def loadReference(self, row):
        item = self.zotWrapTable.zotWrap.refList[row]
        index = self.docType.findText(item["data"]["itemType"], QtCore.Qt.MatchFixedString)
        if index >= 0:
             self.docType.setCurrentIndex(index)
             self.stackedWidget.setCurrentIndex(index)
        self.documentObjects[index].loadItem(item)
        self.selectedRow = row
         
         
    def addReference(self):
        reference = self.documentObjects[self.docType.currentIndex()].getReference() 
        
        if self.updateExisting:        
            self.zotWrapTable.zotLib.update_item(reference)
            item = self.zotWrapTable.zotLib.item(reference["key"])
            self.zotWrapTable.updateItem(item, self.selectedRow)            
        else:
            resp = self.zotWrapTable.zotLib.create_items([reference])
        
            if len(resp["success"]) != 1:
                raise ValueError("Error while trying to add a Zotero record : " + str(resp))
    
            item = self.zotWrapTable.zotLib.item(resp["success"][0])    
    
            self.zotWrapTable.addItem(item)
            
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
        try:
            creatorType = self.creatorsLst[0]["creatorType"] 
        except IndexError:
            print(self.creatorsLst)
            raise
        
        outList = []
        for i in range(self.rowCount()):
            names = ["", ""]
            for j in range(2):
                if not self.item(i, j)  is None:
                    names[j] = self.item(i, j).text()
                    
            if names[0] != "" or names[1] != "" :
                creatorDict = {'creatorType':creatorType,
                               'firstName': names[0], 
                               'lastName': names[1]}
                outList.append(creatorDict)           
                
        return outList



        
    def loadCreatorsLst(self, creatorList):

        for rowNo, creator in enumerate(creatorList):
            if self.rowCount()-1 <= rowNo:
                self.insertRow(self.rowCount())
            self.setItem(rowNo , 0, QtGui.QTableWidgetItem(creator['firstName']))
            self.setItem(rowNo , 1, QtGui.QTableWidgetItem(creator['lastName']))



class IdWgt(QtGui.QWidget):
    
    def __init__(self):
        super(IdWgt, self).__init__()        
        self.idType = QtGui.QComboBox(self)
        self.idType.addItems(["DOI", "PMID", "UNPUBLISHED"])

        self.stackedWidget =  QtGui.QStackedWidget()      
        self.stackedWidget.addWidget(QtGui.QLineEdit())
        self.stackedWidget.addWidget(QtGui.QLineEdit())
        self.stackedWidget.addWidget(QtGui.QLineEdit(str(uuid1())))

        self.stackedWidget.widget(2).setDisabled(True)
        self.idType.activated.connect(self.stackedWidget.setCurrentIndex)

        layout = QtGui.QHBoxLayout(self)
        layout.addWidget(self.idType)
        layout.addWidget(self.stackedWidget)

    
    def setIdToReference(self, reference):
        
        if self.idType.currentText() == "DOI":
            reference["DOI"] = self.stackedWidget.currentWidget().text()
        elif self.idType.currentText() == "PMID":         
            reference["extra"] += "\nPMID:" + self.stackedWidget.currentWidget().text()
        elif self.idType.currentText() == "UNPUBLISHED":        
            reference["extra"] += "\nUNPUBLISHED:" + self.stackedWidget.currentWidget().text()
        else:
            raise ValueError()

        return reference

    def loadReference(self, item):
        if "DOI" in item:
            if item["DOI"] != "":
                index = self.idType.findText("DOI", QtCore.Qt.MatchFixedString)
                if index >= 0:
                    self.idType.setCurrentIndex(index)
                    self.stackedWidget.setCurrentIndex(index)     
                    self.stackedWidget.currentWidget().setText(item["DOI"])
                return
        
        if "PMID" in item["extra"]:
            index = self.idType.findText("PMID", QtCore.Qt.MatchFixedString)
            if index >= 0:
                pmid = item["extra"].split("PMID:")[1].split("\n")[0].strip()
                self.idType.setCurrentIndex(index)
                self.stackedWidget.setCurrentIndex(index)     
                self.stackedWidget.currentWidget().setText(pmid)
            return

        if "UNPUBLISHED" in item["extra"]:
            index = self.idType.findText("UNPUBLISHED", QtCore.Qt.MatchFixedString)
            if index >= 0:
                unpublishedId = item["extra"].split("UNPUBLISHED:")[1].split("\n")[0].strip()
                self.idType.setCurrentIndex(index)
                self.stackedWidget.setCurrentIndex(index)     
                self.stackedWidget.currentWidget().setText(unpublishedId)
            return


        


class DocumentObject:        

    def __init__(self, docItemType, zotWrap):
        self.zotLib = zotWrap.zotLib
        self.reference = deepcopy(zotWrap.itemTemplates[docItemType["itemType"]])

    def getCreatorsWidget(self, creatorsLst):
        return CreatorsWgt(creatorsLst)
        

    def getIdWidget(self):
        return IdWgt()
        

    def getReference(self):
    
        for key, widget in self.widgets.items():
            if key == "Id":
                continue
            if isinstance(self.reference[key], str):
                if key != "DOI":
                    self.reference[key] = str(widget.text())
            elif isinstance(self.reference[key], (dict, list)):
                if key == "creators":    
                    self.reference[key] = widget.getCreatorsLst()
        
        # At the end because it can also overwritten the extra field.
        self.reference = self.widgets["Id"].setIdToReference(self.reference)

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
                    self.widgets[key] = self.getCreatorsWidget(deepcopy(value))
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
        
        
        
    def loadItem(self, item):
        
        # Make sure the item is up-to-date
        item = self.zotLib.item(item["key"])
        
        for key, widget in self.widgets.items():
            if key == "Id":
                continue
            if not key in item["data"]:
                warn("Skipping item fields " + key + 
                     " because it is absent from the Zotero template for this item type.")
                continue
            
            if isinstance(item["data"][key], str):
                if key != "DOI":
                    widget.setText(item["data"][key])
            elif isinstance(self.reference[key], (dict, list)):
                if key == "creators":    
                    widget.loadCreatorsLst(item["data"][key])

        # At the end because it can also overwritten the extra field.
        self.widgets["Id"].loadReference(item["data"])
        
        self.reference = item["data"]


        
        
