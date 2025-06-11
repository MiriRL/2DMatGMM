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

# Stores adjustable parameters for the dectector
class Parameters:
    def __init__(
            self,
            size_threshold: int = 1000,
            min_confidence: float = 0.0,
            use_flatfield: bool = False,
            flatfield_path: str = ""
    ):
        self.size_threshold = size_threshold
        self.min_confidence = min_confidence

        self.use_flatfield = use_flatfield
        self.flatfield_path = flatfield_path
    
    def get_size(self):
        return self.size_threshold

class ParametersLayout(QVBoxLayout):
    def __init__(self, parent: QVBoxLayout):
        super().__init__(parent)

        self.parameters = Parameters()

        

    def get_parameters(self):
        return self.parameters
