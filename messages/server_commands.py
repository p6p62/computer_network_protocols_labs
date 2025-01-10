"""
server_commands.py
Борис Гладышев, 343М, 2025 год
"""

from typing import Callable


class ServerCommand:
    def __init__(self, name: str, description: str, args: list, function: Callable) -> None:
        self.name = name
        self.description = description
        self.args = args
        self.command_function = function

    def convert_to_string(self):
        return f"--{self.name} {' '.join([f'\"{a}\"' for a in self.args])} - {self.description}"

    def execute(self, *args):
        # одним из аргументов является сам сервер
        if len(*args) - 1 == len(self.args):
            self.command_function(*args)


def stop_server(args):
    server = args[0]
    server.stop_server()


def kick_user(args):
    server = args[0]
    username = args[1]
    users = server.client_names
    user_socket = list(users.keys())[list(users.values()).index(username)]
    server.disconnect_client(user_socket)


SERVER_COMMANDS = {
    "stop": ServerCommand("stop", "Остановка сервера", [], stop_server),
    "kick": ServerCommand("kick", "Отключение пользователя с именем NAME", ["NAME"], kick_user)
}
