# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:49:40 2016

@author: oreilly
"""

#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import json

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit


class JSONDlg(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("JSON representations")
        self.setGeometry(100, 300, 1000, 1000)

        # Layout
        layout = QVBoxLayout()

        self.jsonText = QTextEdit(self)
        layout.addWidget(self.jsonText)

        self.setLayout(layout)

    def setJSON(self, objectToDisplay):
        self.jsonText.setText(json.dumps(objectToDisplay.toJSON(), 
                         sort_keys=True, indent=4, separators=(',', ': ')))        
