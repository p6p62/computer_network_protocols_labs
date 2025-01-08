import socket
import select
from config import SETTINGS
import time
from message import Message

class ChatServer:
    def __init__(self, host=SETTINGS['HOST'], port=SETTINGS['PORT']):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.server_socket.setblocking(False)

        self.inputs = [self.server_socket]  # Список сокетов для чтения
        self.clients = {}  # {socket: name}

        print("Для остановки сервера закрой это окно")
        print(f"Server started on {host}:{port}")

    def broadcast(self, message, sender_socket=None, include_sender=False):
        serialized_message = message.serialize()
        for sock in self.clients:
            if include_sender or sock != sender_socket:
                try:
                    sock.sendall(serialized_message.encode('utf-8'))
                except Exception as e:
                    print(f"Failed to send message to {self.clients[sock]}: {e}")

    def handle_new_connection(self):
        client_socket, client_address = self.server_socket.accept()
        client_socket.setblocking(False)
        self.inputs.append(client_socket)
        self.clients[client_socket] = None  # Имя будет установлено позже
        print(f"Connection from {client_address}.")

    def handle_client_message(self, sock):
        try:
            message = sock.recv(1024).decode('utf-8').strip()
            if not message:  # Клиент закрыл соединение
                self.disconnect_client(sock)
                return

            if self.clients[sock] is None:  # Ожидание имени клиента
                self.clients[sock] = message
                print(f"{message} has connected.")
                server_message = Message('S', sender="Server", text_data=f"{message} has joined the chat.")
                self.broadcast(server_message, include_sender=True)
            else:
                name = self.clients[sock]
                chat_message = Message.deserialize(message)
                chat_message.sender = name  # Обновляем имя отправителя
                chat_message.timestamp = int(time.time())  # Обновляем временную метку
                print(f"{chat_message.sender}: {chat_message.text_data}")
                self.broadcast(chat_message, sender_socket=sock, include_sender=True)
        except Exception as e:
            print(f"Error handling client message: {e}")
            self.disconnect_client(sock)

    def disconnect_client(self, sock):
        if sock in self.inputs:
            self.inputs.remove(sock)
        name = self.clients.pop(sock, 'Unknown')
        print(f"{name} has disconnected.")
        server_message = Message('S', sender="Server", text_data=f"{name} has left the chat.")
        self.broadcast(server_message)
        sock.close()

    def stop_server(self):
        print("Stopping server...")
        for sock in self.inputs:
            sock.close()
        self.inputs.clear()
        self.clients.clear()
        print("Server stopped.")

    def run(self):
        try:
            while True:
                readable, _, _ = select.select(self.inputs, [], [])

                for sock in readable:
                    if sock is self.server_socket:
                        self.handle_new_connection()
                    else:
                        self.handle_client_message(sock)
        except KeyboardInterrupt:
            self.stop_server()

if __name__ == "__main__":
    server = ChatServer()
    server.run()
