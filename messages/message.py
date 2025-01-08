import time

class Message:
    def __init__(self, msg_type, sender=None, timestamp=None, text_data=""):
        self.msg_type = msg_type  # Тип сообщения ('C' - чат, 'S' - служебное)
        self.sender = sender  # Идентификатор отправителя (имя клиента)
        self.timestamp = timestamp if timestamp is not None else int(time.time())
        self.text_data = text_data

    def serialize(self):
        return f"{self.msg_type}|{self.sender}|{self.timestamp}|{self.text_data}"

    @staticmethod
    def deserialize(message_str):
        parts = message_str.split('|', 3)
        if len(parts) != 4:
            raise ValueError("Invalid message format")
        msg_type, sender, timestamp, text_data = parts
        return Message(msg_type, sender, int(timestamp), text_data)
