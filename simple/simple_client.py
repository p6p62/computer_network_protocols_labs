"""
simple_client.py
Борис Гладышев, 343М, 2025 год
"""

import socket
from config import SETTINGS

HOST = SETTINGS["HOST"]
PORT = SETTINGS["PORT"]
BUFFER_SIZE = SETTINGS["MAX_BUFFER_SIZE"]

MESSAGE = b"Hello, simple server!"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
    client_socket.connect((HOST, PORT))
    client_socket.sendall(MESSAGE)
    print(f"Отправлено серверу: {MESSAGE.decode('utf-8')}")
    data = client_socket.recv(BUFFER_SIZE)

print(f"Получено с сервера: {data.decode('utf-8')}")