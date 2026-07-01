import logging
import os
import csv
from datetime import datetime
from logging.handlers import RotatingFileHandler
from config import BOT_TOKEN 

class TokenMaskingFormatter(logging.Formatter):

    def format(self, record):
        msg = super().format(record)
        if BOT_TOKEN:
            msg = msg.replace(BOT_TOKEN, "***TOKEN***")
        return msg

def setup_logger(name: str = "bot") -> logging.Logger:

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    # File handler – detailed logs with rotation
    file_handler = RotatingFileHandler(
        "logs/bot.log", maxBytes=5*1024*1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = TokenMaskingFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler – clean output for the terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = TokenMaskingFormatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

# Create the main application logger
logger = setup_logger("bot")


def log_game_event(event_type: str, user_id: int, details: str = "") -> None:

    os.makedirs("logs", exist_ok=True)
    file_exists = os.path.isfile("logs/game_events.csv")
    with open("logs/game_events.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "event_type", "user_id", "details"])
        writer.writerow([datetime.now().isoformat(), event_type, user_id, details])