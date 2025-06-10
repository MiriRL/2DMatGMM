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

class DatabaseTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

