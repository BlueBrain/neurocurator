# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:49:40 2016

@author: oreilly
"""

#!/usr/bin/python3

__author__ = "Christian O'Reilly"

# Import PySide classes
from PySide import QtGui
import json

class JSONDlg(QtGui.QDialog):

    def __init__(self, settings = None, parent=None):
        super(JSONDlg, self).__init__(parent)
        self.setWindowTitle("JSON representations")
        self.setGeometry(100, 300, 1000, 1000)

        # Layout
        layout = QtGui.QVBoxLayout()

        self.jsonText = QtGui.QTextEdit(self)
        layout.addWidget(self.jsonText)

        self.setLayout(layout)

    def setJSON(self, objectToDisplay):
        self.jsonText.setText(json.dumps(objectToDisplay.toJSON(), 
                         sort_keys=True, indent=4, separators=(',', ': ')))        
                
        