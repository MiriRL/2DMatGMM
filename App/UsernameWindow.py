import json
import os

from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget, QDialogButtonBox,QListWidgetItem, QInputDialog, QMessageBox
from PySide6.QtCore import Qt

USERS_JSON = "user_list.json"

class UsernameWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.button = QPushButton("Select User")
        self.button.clicked.connect(self.open_username_window)

        layout = QVBoxLayout()
        layout.addWidget(self.button)

        self.setLayout(layout)

    def open_username_window(self):
        dialog = UsernameWindow(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username = dialog.username_input.text()
            if username:
                self.button.setText(f"User: {username}")
            else:
                self.button.setText("Select User")

class UsernameWindow(QDialog):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setWindowTitle("Select User")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.username_label = QLabel("Username:")
        self.username_input = QListWidget()
        self.username_input.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # Connect a signal for item selection
        self.username_input.itemClicked.connect(self.on_item_clicked)

        # Populate the list with usernames from the Users json file in App
        parent_dir = os.path.abspath(os.path.dirname(__file__))
        self.users_path = os.path.join(parent_dir, USERS_JSON)
        with open(self.users_path, "w") as f:
            json.dump(["dummy user", "dummy user 2"], f)
        
        try:
            self.user_list = json.load(open(self.users_path, "r"))
        except FileNotFoundError:
            self.user_list = ["User list not retrieved"]

        self.username_input.addItem("No User")  # Default empty user
        self.username_input.addItems(self.user_list)

        # Add and remove user buttons
        self.add_user_button = QPushButton("Add new user")
        self.add_user_button.clicked.connect(self.add_new_user)
        self.remove_user_button = QPushButton("Remove user")

        QBtn = (
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def on_item_clicked(self, item: QListWidgetItem):
        # When an item is clicked, set the text of the input field to the item's text
        self.username_input.setCurrentItem(item)
        self.username_input.setFocus()
        self.username_label.setText(f"Selected User: {item.text()}")

    def update_user_list(self):
        with open(self.users_path, "w") as f:
            json.dump(self.user_list, f)

    def add_new_user(self):
        username, ok = QInputDialog.getText(self, "Create new user", "Enter username:")

        if ok and username and username not in self.user_list:
            self.user_list.append(username)
            self.username_input.addItem(username)
            self.update_user_list()

    def remove_user(self):
        username = self.username_input.currentItem().text()
        if username is None:
            QMessageBox.warning(self, "Warning", "No user selected to remove.")
            return
        if username in self.user_list:
            reply = QMessageBox.question(
                self, "Confirm Removal",
                f"Are you sure you want to remove the user '{username}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            self.user_list.remove(username)
            for i in range(self.username_input.count()):
                if self.username_input.item(i).text() == username:
                    self.username_input.takeItem(i)
                    break
            self.update_user_list()