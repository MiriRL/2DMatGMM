# Original code from The Qt Company Ltd. 2022
# Modified for personal use
import sys
import json
import os

from PySide6.QtCore import QFileInfo
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QApplication,
    QDialog,
    QTabWidget,
    QLineEdit,
    QPushButton,
    QFrame,
    QListWidget,
    QFileDialog,
)


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
        
        # Get the models_info file from one level up in the Models folder
        parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        model_path = os.path.join(parent_dir, "Models/models_info.json")
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

        main_layout = QVBoxLayout()
        main_layout.addWidget(select_file_label)
        main_layout.addWidget(self.browse_file_button)
        main_layout.addWidget(select_model_label)
        main_layout.addWidget(self.models_list_box)
        main_layout.addWidget(model_description_label)
        main_layout.addWidget(self.model_description)
        main_layout.addStretch(1)
        self.setLayout(main_layout)
        

    # Function written by ChatGPT
    def browse_file(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.selected_folder_path = folder_path
            self.browse_file_button.setText(self.truncate_path(folder_path))
            print(f"Selected file: {self.selected_folder_path}")

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
        else:
            curr_model = self.models[curr_text]
            self.model_description.setText(curr_model["Description"])


class DatabaseTab(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        # top_label = QLabel("Open with:")

        # applications_list_box = QListWidget()
        # applications = []

        # for i in range(1, 31):
        #     applications.append(f"Application {i}")
        # applications_list_box.insertItems(0, applications)

        # if not file_info.suffix():
        #     always_check_box = QCheckBox(
        #         "Always use this application to open this type of file"
        #     )
        # else:
        #     always_check_box = QCheckBox(
        #         f"Always use this application to open files "
        #         f"with the extension {file_info.suffix()}"
        #     )

        # layout = QVBoxLayout()
        # layout.addWidget(top_label)
        # layout.addWidget(applications_list_box)
        # layout.addWidget(always_check_box)
        # self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    tab_dialog = TabDialog()
    tab_dialog.show()

    sys.exit(app.exec())