# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:49:40 2016

@author: oreilly
"""

#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui, QtCore


class AddOntoTermDlg(QtGui.QDialog):

    def __init__(self, parent=None):
        super(AddOntoTermDlg, self).__init__(parent)
        self.setWindowTitle("Addition of a new ontology term")
        self.setGeometry(100, 300, 1000, 1000)




        self.warningMsg = QtGui.QLabel("Remember: ", self)

        self.addingGroup = QtGui.QGroupBox("Adding a new ontology term")
        addingLayout = QtGui.QVBoxLayout(self.addingGroup)
        addingLayout.addWidget(self.warningMsg)



        self.suggestionGroup = QtGui.QGroupBox("Existing ontological term suggestions")
        suggestionLayout = QtGui.QVBoxLayout(self.suggestionGroup)
        #suggestionLayout.addWidget(self.warningMsg)



        # Layout
        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.addingGroup)
        layout.addWidget(self.suggestionGroup)

        self.setLayout(layout)
      
                
        
