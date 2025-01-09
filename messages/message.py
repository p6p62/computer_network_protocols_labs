import time


class Message:
    CHAT_MESSAGE = 'C'
    SERVICE_TEXT_MESSAGE = 'S'
    USERS_UPDATE_MESSAGE = 'U'

    def __init__(self, msg_type, sender=None, timestamp=None, text_data=""):
        self.msg_type = msg_type
        self.sender = sender
        self.timestamp = \
            timestamp if timestamp is not None else int(time.time())
        self.text_data = text_data

    def get_formatted_message_time(self) -> str:
        return time.strftime("%H:%M:%S", time.localtime(int(self.timestamp)))

    def serialize(self):
        return f"{self.msg_type}|{self.sender}|{self.timestamp}|{self.text_data}"

    @staticmethod
    def deserialize(message_str):
        parts = message_str.split('|', 3)
        if len(parts) != 4:
            raise ValueError("Invalid message format")
        msg_type, sender, timestamp, text_data = parts
        return Message(msg_type, sender, int(timestamp), text_data)
