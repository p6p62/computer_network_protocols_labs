"""
server.py
Борис Гладышев, 343М, 2025 год
"""

import socket
import select
import sys
import threading
from config import SETTINGS
import time
import json
from message import Message
from logger import Logger

from PyQt6.QtWidgets import QApplication
from client import ChatClient

from server_commands import SERVER_COMMANDS


class ChatServer:
    BUFFER_SIZE = SETTINGS["MAX_BUFFER_SIZE"]
    ENCODING = SETTINGS["ENCODING"]
    SERVER_NAME = "Server"

    def __init__(self, host=SETTINGS['HOST'], port=SETTINGS['PORT']):
        self.logger = Logger(
            log_dir=SETTINGS["SERVER_LOG_DIR"], log_file=SETTINGS["SERVER_LOG_FILE"])

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)

        self.inputs = [self.server_socket]  # Список сокетов для прослушивания
        self.client_names = {}

        print("Close this terminal for stop server")
        self.log(f"Server started on {host}:{port}")

    def create_admin(self):
        # для гарантированного старта сервера к моменту создания панели администратора
        SERVER_START_WAIT_TIMEOUT = 1
        time.sleep(SERVER_START_WAIT_TIMEOUT)

        app = QApplication(sys.argv)

        client = ChatClient("SERVER_ADMIN")
        client.add_admin_hint()
        client.show()
        status = client.connect_to_server()
        if status == 0:
            self.admin_socket = self.inputs[1]
            sys.exit(app.exec())

    def log(self, log_text):
        print(log_text)
        self.logger.log(log_text)

    def broadcast(self, message, sender_socket=None, include_sender=False):
        serialized_message = message.serialize()
        for sock in self.client_names:
            if include_sender or sock != sender_socket:
                try:
                    sock.sendall(serialized_message.encode(
                        ChatServer.ENCODING))
                except Exception as e:
                    self.log(
                        f"Failed to send message to {self.client_names[sock]}: {e}")

    def handle_new_connection(self):
        client_socket, client_address = self.server_socket.accept()
        client_socket.setblocking(False)
        self.inputs.append(client_socket)
        self.client_names[client_socket] = None  # Имя будет установлено позже
        self.log(f"Connection from {client_address}.")

    def process_admin_message(self, message: Message):
        text = message.text_data
        is_command = text.startswith("--")
        if not is_command:
            return
        command_name, *args = text.removeprefix("--").split(' ')
        command = SERVER_COMMANDS[command_name.lower()]
        command.execute([server, *args])

    def handle_client_message(self, client_socket: socket.socket):
        try:
            message = client_socket.recv(ChatServer.BUFFER_SIZE).decode(
                ChatServer.ENCODING).strip()
            if not message:  # Клиент закрыл соединение
                self.disconnect_client(client_socket)
                return

            if self.client_names[client_socket] is None:
                # Установка имени (первое сообщение нового пользователя - это всегда имя)
                self.client_names[client_socket] = message
                self.log(f"{message} has connected.")
                server_message = Message(
                    Message.SERVICE_TEXT_MESSAGE,
                    sender=ChatServer.SERVER_NAME,
                    text_data=f"{message} теперь с нами")
                self.broadcast(server_message, include_sender=True)
                self.send_users_list()
            else:
                name = self.client_names[client_socket]
                chat_message = Message.deserialize(message)

                if client_socket == self.admin_socket:
                    self.process_admin_message(chat_message)

                chat_message.sender = name  # Обновление имени отправителя на известное серверу
                # Временную метку всегда ставит сервер
                chat_message.timestamp = int(time.time())
                self.log(f"{chat_message.sender}: {chat_message.text_data}")
                self.broadcast(
                    chat_message, sender_socket=client_socket, include_sender=True)
        except Exception as e:
            self.log(f"{e}")
            self.disconnect_client(client_socket)

    def send_users_list(self):
        users_data = json.dumps(list(self.client_names.values()))
        server_message = Message(
            Message.USERS_UPDATE_MESSAGE, sender=ChatServer.SERVER_NAME, text_data=users_data)
        self.broadcast(server_message)

    def disconnect_client(self, client_socket):
        name = self.client_names.get(client_socket, 'Unknown')
        server_message = Message(Message.SERVICE_TEXT_MESSAGE,
                                 sender=ChatServer.SERVER_NAME, text_data=f"{name} покидает нас")
        self.broadcast(server_message)
        self.client_names.pop(client_socket, 'Unknown')
        self.send_users_list()
        if client_socket in self.inputs:
            self.inputs.remove(client_socket)
        client_socket.close()
        self.log(f"{name} has disconnected.")

    def stop_server(self):
        self.log("Stopping server...")
        for sock in self.inputs:
            sock.close()
        self.inputs.clear()
        self.client_names.clear()
        self.log("Server stopped.")

    def run(self):
        try:
            while True:
                readable, _, _ = select.select(self.inputs, [], [])

                for input_socket in readable:
                    if input_socket is self.server_socket:
                        self.handle_new_connection()
                    else:
                        self.handle_client_message(input_socket)
        finally:
            self.stop_server()


if __name__ == "__main__":
    server = ChatServer()
    threading.Thread(target=server.create_admin, daemon=True).start()
    server.run()
