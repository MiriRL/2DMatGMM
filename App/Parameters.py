from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QSpinBox,
    QLineEdit,
)

# Stores adjustable parameters for the dectector
class Parameters:
    def __init__(
            self,
            size_threshold: int = 1000,
            min_confidence: float = 0.0,
            use_flatfield: bool = False,
            flatfield_path: str = "",
            save_to_database: bool = True
    ):
        self.size_threshold = size_threshold
        self.min_confidence = min_confidence

        self.use_flatfield = use_flatfield
        self.flatfield_path = flatfield_path

        self.save_to_database = save_to_database

    def get_size(self):
        return self.size_threshold

class ParametersWidget(QGroupBox):
    def __init__(self, parent = None):
        super().__init__(parent)
        self.setTitle("Optional Parameters")
        self.parameters = Parameters()

        # size_threshold and min_confidence go in their own horizontal layout within the vertical layout

        self.use_database = QCheckBox("Save flakes to database")
        self.use_database.setChecked(True)
        self.use_database.toggled.connect(self.set_use_database)

        min_confidence_label = QLabel("Set minimum confidence value (%):")
        self.set_min_confidence = QSpinBox()
        self.set_min_confidence.setRange(0, 99)
        self.set_min_confidence.setValue(self.parameters.min_confidence)
        self.set_min_confidence.setSingleStep(1)
        self.set_min_confidence.valueChanged.connect(self.update_min_confidence)

        size_threshold_label = QLabel("Set minimum size threshold (pixels):")
        self.set_size_threshold = QLineEdit(str(self.parameters.size_threshold))
        double_validator = QDoubleValidator(-100.0, 100.0, 2, self.set_size_threshold)
        self.set_size_threshold.setValidator(double_validator)
        self.set_size_threshold.textChanged.connect(self.on_text_changed)

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

        layout = QGridLayout()
        layout.addWidget(self.use_database, 1, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(min_confidence_label, 2, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.set_min_confidence, 2, 2)
        layout.addWidget(size_threshold_label, 3, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.set_size_threshold, 3, 2)
        layout.addWidget(self.use_flatfield, 4, 1, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.select_file_label, 5, 1, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.browse_file_button, 5, 2, -1, -1)
        
        layout.setColumnStretch(2, 1)  # Stretch the last column to fill space
        layout.setVerticalSpacing(10)  # Add vertical spacing between rows
        self.setLayout(layout)

    def get_parameters(self):
        return self.parameters
    
    def set_use_flatfield(self, checked):
        self.parameters.use_flatfield = checked
        self.select_file_label.setVisible(checked)
        self.browse_file_button.setVisible(checked)

    def set_use_database(self, checked):
        self.parameters.save_to_database = checked

    def update_min_confidence(self, value):
        self.parameters.min_confidence = value

    def on_text_changed(self, text):
        try:
            value = int(text)
            if value < 0:
                value = 0
            elif value > 10000:
                value = 10000
            self.parameters.size_threshold = value
            self.set_size_threshold.setText(str(value))
        except ValueError:
            # If the input is not a valid integer, reset to the previous valid value
            if text == "":
                # If the input is empty, reset to default value
                self.parameters.size_threshold = Parameters().size_threshold
            self.set_size_threshold.setText(str(self.parameters.size_threshold))
    
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
