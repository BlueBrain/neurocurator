# -*- coding: utf-8 -*-
"""
Created on Mon Sep  5 11:49:40 2016

@author: oreilly
"""

#!/usr/bin/python3

__author__ = "Christian O'Reilly"

from PyQt5.QtWidgets import QDialog, QLabel, QGroupBox, QVBoxLayout, QHBoxLayout


class AddOntoTermDlg(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Addition of a new ontology term")
        self.setGeometry(100, 300, 1000, 1000)

        self.warningMsg = QLabel("Remember: ", self)

        self.addingGroup = QGroupBox("Adding a new ontology term")
        addingLayout = QVBoxLayout(self.addingGroup)
        addingLayout.addWidget(self.warningMsg)

        self.suggestionGroup = QGroupBox("Existing ontological term suggestions")

        # Layout
        layout = QHBoxLayout()
        layout.addWidget(self.addingGroup)
        layout.addWidget(self.suggestionGroup)

        self.setLayout(layout)
