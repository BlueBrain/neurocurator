#!/usr/bin/python3

__author__ = "Pierre-Alexandre Fonta"

import os
import sys


def working_directory():
    """Return the working directory according to it being bundled/frozen."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(__file__)
