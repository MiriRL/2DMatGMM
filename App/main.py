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

from run_detector import run_algorithm

# Model path relative to the parent directory
MODEL_PATH = "Models/models_info.json"


class TabDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        tab_widget = QTabWidget()

        tab_widget.addTab(InfoTab(self), "Help")
        tab_widget.addTab(DetectorTab(self), "Detect Flakes")
        tab_widget.addTab(DatabaseTab(self), "Database")


        main_layout = QVBoxLayout()
        main_layout.addWidget(tab_widget)
        self.setLayout(main_layout)
        self.setWindowTitle("2DMatGMM")
        self.resize(1000, 500)


class InfoTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)



class DetectorTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        # Placeholder for selected variables
        self.selected_folder_path = None
        self.curr_model_is_valid = False
        
        # Get the models_info file from one level up in the Models folder
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        model_path = os.path.join(parent_dir, MODEL_PATH)
        self.models = json.load(open(model_path, "r"))

        select_file_label = QLabel("Select the folder containing the images:")
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

        select_model_label = QLabel("Select the model you want to use:")
        self.models_list_box = QComboBox()
        
        self.models_list_box.addItem("--")  # This acts as a default "unselected" option
        self.models_list_box.addItems(self.models.keys())
        self.models_list_box.currentTextChanged.connect(self.select_model)

        model_description_label = QLabel("Model Description:")
        self.model_description = QLabel("No model selected.")
        self.model_description.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)

        self.debugging_text = QLabel("")

        self.run_button = QPushButton("RUN")
        self.run_button.clicked.connect(self.run_model)
        self.run_button.setStyleSheet("""
            QPushButton {
                border: 1px solid gray;
                background-color: #39e75f;
                color: black;
                font-weight: bold; 
                font-size: 16px;
                border: 2px solid gray; 
                border-radius: 5px;
                padding: 12px 24px; 
                text-align: center; 
            }
            QPushButton:hover {
                background-color: #2fba4d;      /* Slightly darker on hover */
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.addWidget(select_file_label)
        main_layout.addWidget(self.browse_file_button)
        main_layout.addWidget(select_model_label)
        main_layout.addWidget(self.models_list_box)
        main_layout.addWidget(model_description_label)
        main_layout.addWidget(self.model_description)
        main_layout.addStretch()
        main_layout.addWidget(self.debugging_text)
        main_layout.addWidget(self.run_button, alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        self.setLayout(main_layout)
        

    # Function written by ChatGPT
    def browse_file(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.selected_folder_path = folder_path
            self.browse_file_button.setText(self.truncate_path(folder_path))

    # Function written by ChatGPT
    def truncate_path(self, path, max_length = 40):
        if len(path) <= max_length:
            return path
        else:
            # Keep the start and end, cut out the middle
            start = path[:20]
            end = path[-(max_length - len(start) - 3):]
            return f"{start}...{end}"
        
    def select_model(self):
        curr_text = self.models_list_box.currentText()
        if curr_text not in self.models:
            self.model_description.setText("No model selected.")
            self.curr_model_is_valid = False
        else:
            curr_model = self.models[curr_text]
            self.model_description.setText(curr_model["Description"])
            self.curr_model_is_valid = True
    
    def run_model(self):
        if self.selected_folder_path is None:
            self.debugging_text.setText("Select a folder.")
            return
        if self.curr_model_is_valid and os.path.isdir(self.selected_folder_path):
            self.debugging_text.setText("Running current model.")
            curr_model = self.models[self.models_list_box.currentText()]
            model_file_name = curr_model["File Name"]
            run_algorithm(model_file_name, self.selected_folder_path)
        else:
            self.debugging_text.setText("Selected model or selected folder are not valid.")


class DatabaseTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    tab_dialog = TabDialog()
    tab_dialog.show()

    sys.exit(app.exec())