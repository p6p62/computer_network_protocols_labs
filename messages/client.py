"""
client.py
Борис Гладышев, 343М, 2025 год
"""

import sys
import socket
import json
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit,
    QPushButton, QVBoxLayout, QWidget, QLabel, QListWidget, QInputDialog
)
from PyQt6.QtGui import QColorConstants
from config import SETTINGS
from message import Message
from logger import Logger
from server_commands import SERVER_COMMANDS


class ChatClient(QMainWindow):
    BUFFER_SIZE = SETTINGS["MAX_BUFFER_SIZE"]
    ENCODING = SETTINGS["ENCODING"]
    DISCONNECTED_TEXT = "Нет подключения к серверу"
    CONNECTED_TEXT = "Подключено к серверу"

    def __init__(self, username=None, host=SETTINGS['HOST'], port=SETTINGS['PORT']):
        super().__init__()
        self.logger = Logger(log_dir=SETTINGS["CLIENT_LOG_DIR"],
                             log_file=SETTINGS["CLIENT_LOG_FILE"])
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = username

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Чат")

        self.admin_hint = None  # панель команд администратора

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Введи сообщение...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Отправить [Enter]")
        self.send_button.clicked.connect(self.send_message)

        self.status_label = QLabel(ChatClient.DISCONNECTED_TEXT)

        self.clients_list = QListWidget()

        self.username_label = QLabel("<ваше имя>")

        layout = QVBoxLayout()
        layout.addWidget(self.chat_display)
        layout.addWidget(self.username_label)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        layout.addWidget(QLabel("Подключенные пользователи:"))
        layout.addWidget(self.clients_list)
        layout.addWidget(self.status_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.message_input.setFocus()

    def add_admin_hint(self):
        if self.admin_hint is None:
            commands = "\n".join([c.convert_to_string()
                                 for c in list(SERVER_COMMANDS.values())])
            admin_hint_label = QLabel(commands)
            self.centralWidget().layout().addWidget(admin_hint_label)

    def fill_username(self, name: str):
        self.username_label.setText(self.name)
        self.setWindowTitle(f"{self.windowTitle()} [{name}]")

    def connect_to_server(self) -> int:
        return_value = 0
        try:
            self.socket.connect((self.host, self.port))
            self.status_label.setText(ChatClient.CONNECTED_TEXT)
            self.log(f"Connected to server ({self.host}:{self.port})")

            if self.name is None:
                self.name = self.get_user_name()
            self.fill_username(self.name)
            self.log(f"User entered name: {self.name}")

            threading.Thread(target=self.receive_messages, daemon=True).start()

            # Send the user name to the server
            self.socket.sendall(self.name.encode(ChatClient.ENCODING))
        except Exception as e:
            return_value = 1
            self.log(f"Ошибка подключения к серверу: {e}")
        return return_value

    def log(self, log_text):
        print(log_text)
        self.logger.log(log_text)

    def get_user_name(self):
        name, ok = QInputDialog.getText(
            self, "Ввод имени", "Введи своё имя для чата:")
        if ok and name:
            return name
        else:
            self.close()

    def send_message(self):
        text = self.message_input.text().strip()
        if text:
            message = Message(msg_type=Message.CHAT_MESSAGE,
                              sender=self.name, text_data=text)
            self.socket.sendall(
                message.serialize().encode(ChatClient.ENCODING))
            self.message_input.clear()
            self.log(f"Send message from {self.name}")

    def print_text_message(self, message_str: str):
        self.chat_display.append(message_str)

    def print_server_message(self, message_str):
        text_color = self.chat_display.textColor()
        self.chat_display.setTextColor(QColorConstants.DarkGray)
        self.print_text_message(message_str)
        self.chat_display.setTextColor(text_color)

    def get_message_str(self, message: Message) -> str:
        message_time = message.get_formatted_message_time()
        return f"{message_time} [{message.sender}] {message.text_data}"

    def process_message(self, message: Message):
        message_str = self.get_message_str(message)
        if message.msg_type == Message.CHAT_MESSAGE:
            self.print_text_message(message_str)
        elif message.msg_type == Message.SERVICE_TEXT_MESSAGE:
            self.print_server_message(message_str)
        elif message.msg_type == Message.USERS_UPDATE_MESSAGE:
            self.update_users_list(message.text_data)

    def receive_messages(self):
        while True:
            try:
                data = self.socket.recv(
                    ChatClient.BUFFER_SIZE).decode(ChatClient.ENCODING)
                if not data:
                    break
                message = Message.deserialize(data)
                self.process_message(message)
            except Exception as e:
                self.log(f"{e}")
                self.status_label.setText(ChatClient.DISCONNECTED_TEXT)
                break

    def update_users_list(self, users_list):
        users = json.loads(users_list)
        self.clients_list.clear()
        self.clients_list.addItems(users)

    def closeEvent(self, event):
        self.socket.close()
        self.log(f"{self.name} disconnect from server")
        self.log(f"{self.name} has closed client")
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    client = ChatClient()
    client.show()
    status = client.connect_to_server()
    if status == 0:
        sys.exit(app.exec())
