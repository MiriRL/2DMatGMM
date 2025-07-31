import sys
import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QApplication,
    QDialog,
    QTabWidget,
    QPushButton,
    QFrame,
    QFileDialog,
)

# The database tab is unimplemented. Code to locally visualize the Box database can be added here.
# Recommended inspiration for the database GUI is the 2DMatGMM website. 
class DatabaseTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

# How to access data from Box (must be locally downloaded and logged in on the computer. Note: not tested.)
#
# The directory should be: database_dir = Path.home() / "Box" / "Quantum Device Lab" / "External Optical Cataloger"
# This could change depending on the computer. This path worked on the external cataloger computer in lab 325 as of summer 2025.
#
# From this directory, the file structure appears as follows (as of summer 2025):
# Folder for each individual run output > annotated images and JSON file with flake information
#
# The folders are names with the data and time 2DMatGMM was run. If a user is chosen, the username appears first.
# The code for this saving process can be found in the App/DetectorManager.py file.