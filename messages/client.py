import sys
import socket
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit,
    QPushButton, QVBoxLayout, QWidget, QLabel, QListWidget, QInputDialog
)
from PyQt6.QtCore import Qt
from config import SETTINGS
from message import Message

class ChatClient(QMainWindow):
    def __init__(self, host=SETTINGS['HOST'], port=SETTINGS['PORT']):
        super().__init__()
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.name = None

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Chat Client")

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        self.status_label = QLabel("Disconnected")

        self.clients_list = QListWidget()

        layout = QVBoxLayout()
        layout.addWidget(self.chat_display)
        layout.addWidget(self.message_input)
        layout.addWidget(self.send_button)
        layout.addWidget(QLabel("Connected Clients:"))
        layout.addWidget(self.clients_list)
        layout.addWidget(self.status_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        self.message_input.setFocus()

    def connect_to_server(self):
        try:
            self.socket.connect((self.host, self.port))
            self.status_label.setText("Connected")
            self.name = self.get_user_name()

            threading.Thread(target=self.receive_messages, daemon=True).start()

            # Send the user name to the server
            self.socket.sendall(self.name.encode('utf-8'))
        except Exception as e:
            self.chat_display.append(f"Error connecting to server: {e}")

    def get_user_name(self):
        name, ok = QInputDialog.getText(self, "Enter Name", "Enter your chat name:")
        if ok and name:
            return name
        else:
            self.close()

    def send_message(self):
        text = self.message_input.text().strip()
        if text:
            message = Message(msg_type='C', sender=self.name, text_data=text)
            self.socket.sendall(message.serialize().encode('utf-8'))
            self.message_input.clear()

    def receive_messages(self):
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break

                message = Message.deserialize(data)
                if message.msg_type == 'C':
                    self.chat_display.append(f"[{message.sender}] {message.text_data}")
                elif message.msg_type == 'S':
                    self.chat_display.append(f"[Server] {message.text_data}")

                if message.msg_type == 'S' and "connected clients" in message.text_data.lower():
                    self.update_clients_list(message.text_data)

            except Exception as e:
                self.chat_display.append(f"Error receiving message: {e}")
                break

    def update_clients_list(self, clients_info):
        clients = clients_info.split(':', 1)[-1].strip().split(',')
        self.clients_list.clear()
        self.clients_list.addItems(clients)

    def closeEvent(self, event):
        self.socket.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    client = ChatClient()
    client.show()

    client.connect_to_server()

    sys.exit(app.exec())