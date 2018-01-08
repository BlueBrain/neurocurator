__author__ = "Pierre-Alexandre Fonta"

import os
import sys

from PySide.QtCore import Qt
from PySide.QtGui import QFormLayout


def working_directory():
    """Return the working directory according to it being bundled/frozen."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)


def configure_form_layout(form_layout):
    """Configure in an harmonized way QFormLayouts."""
    form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
    form_layout.setLabelAlignment(Qt.AlignLeft)
    form_layout.setRowWrapPolicy(QFormLayout.DontWrapRows)
