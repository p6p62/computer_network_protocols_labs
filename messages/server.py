import socket
import select
import sys
from config import SETTINGS
import time
import json
from message import Message
from logger import Logger

class ChatServer:
    BUFFER_SIZE = SETTINGS["MAX_BUFFER_SIZE"]
    ENCODING = SETTINGS["ENCODING"]
    SERVER_NAME = "Server"

    def __init__(self, host=SETTINGS['HOST'], port=SETTINGS['PORT']):
        self.logger = Logger(log_dir=SETTINGS["SERVER_LOG_DIR"], log_file=SETTINGS["SERVER_LOG_FILE"])

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)


        self.inputs = [self.server_socket]  # Список сокетов для прослушивания
        self.client_names = {}

        print("Close this terminal for stop server")
        self.log(f"Server started on {host}:{port}")

    def log(self, log_text):
        print(log_text)
        self.logger.log(log_text)

    def broadcast(self, message, sender_socket=None, include_sender=False):
        serialized_message = message.serialize()
        for sock in self.client_names:
            if include_sender or sock != sender_socket:
                try:
                    sock.sendall(serialized_message.encode(ChatServer.ENCODING))
                except Exception as e:
                    self.log(f"Failed to send message to {self.client_names[sock]}: {e}")

    def handle_new_connection(self):
        client_socket, client_address = self.server_socket.accept()
        client_socket.setblocking(False)
        self.inputs.append(client_socket)
        self.client_names[client_socket] = None  # Имя будет установлено позже
        self.log(f"Connection from {client_address}.")

    def handle_client_message(self, client_socket: socket.socket):
        try:
            message = client_socket.recv(ChatServer.BUFFER_SIZE).decode(ChatServer.ENCODING).strip()
            if not message:  # Клиент закрыл соединение
                self.disconnect_client(client_socket)
                return

            if self.client_names[client_socket] is None:  # Установка имени клиента
                self.client_names[client_socket] = message
                self.log(f"{message} has connected.")
                server_message = Message(Message.SERVICE_TEXT_MESSAGE, sender=ChatServer.SERVER_NAME, text_data=f"{message} теперь с нами")
                self.broadcast(server_message, include_sender=True)
                self.send_users_list()
            else:
                name = self.client_names[client_socket]
                chat_message = Message.deserialize(message)
                chat_message.sender = name  # Обновление имени отправителя на известное серверу
                chat_message.timestamp = int(time.time())  # Временную метку всегда ставит сервер
                self.log(f"{chat_message.sender}: {chat_message.text_data}")
                self.broadcast(chat_message, sender_socket=client_socket, include_sender=True)
        except Exception as e:
            self.log(f"{e}")
            self.disconnect_client(client_socket)

    def send_users_list(self):
        users_data = json.dumps(list(self.client_names.values()))
        server_message = Message(Message.USERS_UPDATE_MESSAGE, sender=ChatServer.SERVER_NAME, text_data=users_data)
        self.broadcast(server_message)

    def disconnect_client(self, sock):
        if sock in self.inputs:
            self.inputs.remove(sock)
        name = self.client_names.pop(sock, 'Unknown')
        self.log(f"{name} has disconnected.")
        server_message = Message(Message.SERVICE_TEXT_MESSAGE, sender=ChatServer.SERVER_NAME, text_data=f"{name} покидает нас")
        self.broadcast(server_message)
        self.send_users_list()
        sock.close()

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

                for sock in readable:
                    if sock is self.server_socket:
                        self.handle_new_connection()
                    else:
                        self.handle_client_message(sock)
        finally:
            self.stop_server()

if __name__ == "__main__":
    server = ChatServer()
    server.run()
