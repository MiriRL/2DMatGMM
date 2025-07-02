import json
import os

from PySide6.QtWidgets import QDialog, QLabel, QListWidget, QPushButton, QVBoxLayout, QWidget, QDialogButtonBox,QListWidgetItem, QInputDialog, QMessageBox, QHBoxLayout
from PySide6.QtCore import Qt, Signal

USERS_JSON = "user_list.json"

class UsernameWidget(QWidget):
    """A widget that allows the user to select a username from a list or create a new one."""
    user_selected = Signal(str)

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
            username = dialog.username_input.currentItem().text() if dialog.username_input.currentItem() else None
            # Update the button text with the selected username
            if username:
                self.button.setText(f"{username}")
                if username == "No User" or username == "User list not retrieved":
                    self.user_selected.emit(None)  # If the default user or error user is selected, emit None
                else:
                    self.user_selected.emit(username)  # If a valid user is selected, emit the username
            else:
                self.button.setText("Select User")
                self.user_selected.emit(None)  # If no user is selected, emit None

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
        self.remove_user_button.clicked.connect(self.remove_user)

        # A horizontal layout for the edit user list buttons
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.add_user_button)
        h_layout.addWidget(self.remove_user_button)
        edit_container = QWidget()
        edit_container.setLayout(h_layout)

        QBtn = (
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_input)
        layout.addWidget(edit_container)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)

    def on_item_clicked(self, item: QListWidgetItem):
        # When an item is clicked, set the text of the input field to the item's text
        self.username_input.setCurrentItem(item)
        self.username_input.setFocus()
        self.username_label.setText(f"Selected User: {item.text()}")

    def update_user_list(self):
        # Sort the user list alphabetically then overwrite the json with the new list
        self.user_list.sort(key=str.lower)  # Sort case-insensitively
        with open(self.users_path, "w") as f:
            json.dump(self.user_list, f)

    def add_new_user(self):
        username, ok = QInputDialog.getText(self, "Create new user. Use only letters, numbers, and underscores. No spaces.", "Enter username:")

        if ok and self.check_valid_username(username):
            self.user_list.append(username)
            self.username_input.insertItem(1, username)  # Insert at position 1 to keep "No User" at the top
            self.update_user_list()

    def check_valid_username(self, username: str) -> bool:
        """Check if the username is valid (not empty, not already in the list, and usable as a file name)."""
        if not username:
            QMessageBox.warning(self, "Warning", "Username cannot be empty.")
            return False
        if username in self.user_list:
            QMessageBox.warning(self, "Warning", f"Username '{username}' already exists.")
            return False
        if not username.isidentifier():
            QMessageBox.warning(self, "Warning", f"Username '{username}' is not a valid username. Only letters, numbers, and underscores are allowed.")
            return False
        if len(username) > 20:
            QMessageBox.warning(self, "Warning", "Username cannot be longer than 20 characters.")
            return False
        return True

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