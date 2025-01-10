"""
logger.py
Борис Гладышев, 343М, 2025 год
"""

import os
from datetime import datetime


class Logger:
    def __init__(self, log_dir, log_file):
        self.LOG_DIR = log_dir
        self.LOG_FILE = log_file
        self.LOG_PATH = os.path.join(self.LOG_DIR, self.LOG_FILE)
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)
        if not os.path.exists(self.LOG_PATH):
            with open(self.LOG_PATH, 'w') as f:
                f.write("# Log File Created: " +
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")

    def log(self, message):
        self._ensure_log_file_exists()
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.LOG_PATH, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
