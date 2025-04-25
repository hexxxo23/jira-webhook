import os
import time
import logging
from logging.handlers import TimedRotatingFileHandler

# Set timezone ke Asia/Jakarta
os.environ['TZ'] = 'Asia/Jakarta'
time.tzset()

# Pastikan folder logs ada
log_directory = "storage/logs"
os.makedirs(log_directory, exist_ok=True)

# File handler: rotasi tiap tengah malam, simpan 7 hari
LOG_FILE = os.path.join(log_directory, "app.log")
file_handler = TimedRotatingFileHandler(
    LOG_FILE, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)

# Stream handler (console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(stream_handler)
