import socket
from config import SETTINGS

HOST = SETTINGS["HOST"]
PORT = SETTINGS["PORT"]
BUFFER_SIZE = SETTINGS["MAX_BUFFER_SIZE"]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    client_socket, address = server_socket.accept()
    with client_socket:
        print(f"Установлено соединение с {address}")
        while True:
            data = client_socket.recv(BUFFER_SIZE)
            if not data:
                break
            print(f"Получено сообщение: {data.decode('utf-8')}")
            client_socket.sendall(b"I receive your message: "+ data)