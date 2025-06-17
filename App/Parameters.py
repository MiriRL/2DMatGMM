from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QHBoxLayout
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

class ParametersWidget(QWidget):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.parameters = Parameters()

        # size_threshold and min_confidence go in their own horizontal layout within the vertical layout

        h_layout = QHBoxLayout()

        self.use_flatfield = QCheckBox("Use flatfield image")
        self.use_flatfield.toggled.connect(self.set_use_flatfield)

        self.select_file_label = QLabel("Select the flatfield file:")
        self.browse_file_button = QPushButton("Browse files")
        self.browse_file_button.clicked.connect(self.browse_file)
        self.browse_file_button.setStyleSheet("""
            QPushButton {
                border: 1px solid gray;
                background-color: #f0f0f0;
                color: black;
                padding: 4px;
            }
        """)
        self.select_file_label.setVisible(False)  # Initial state is off
        self.browse_file_button.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.use_flatfield)
        layout.addWidget(self.select_file_label)
        layout.addWidget(self.browse_file_button)
        self.setLayout(layout)

    def get_parameters(self):
        return self.parameters
    
    def set_use_flatfield(self, checked):
        self.parameters.use_flatfield = checked
        self.select_file_label.setVisible(checked)
        self.browse_file_button.setVisible(checked)
    
    # Function written by ChatGPT
    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_path:
            self.parameters.flatfield_path = file_path
            self.browse_file_button.setText(self.truncate_path(file_path))

    # Function written by ChatGPT
    def truncate_path(self, path, max_length = 50):
        if len(path) <= max_length:
            return path
        else:
            # Keep the start and end, cut out the middle
            start = path[:20]
            end = path[-(max_length - len(start) - 3):]
            return f"{start}...{end}"
