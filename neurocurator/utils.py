__author__ = "Pierre-Alexandre Fonta"

import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFormLayout


def package_directory():
    """Return the absolute path to the directory containing the package files."""
    return os.path.abspath(os.path.dirname(__file__))


def configure_form_layout(form_layout):
    """Configure in an harmonized way QFormLayouts."""
    form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    form_layout.setLabelAlignment(Qt.AlignLeft)
    form_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
