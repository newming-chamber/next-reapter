import logging
import os
from datetime import datetime
import pytz
from .config import directory_path, env


class KSTFormatter(logging.Formatter):
    def converter(self, timestamp):
        # Convert to KST timezone
        kst = pytz.timezone("Asia/Seoul")
        dt = datetime.fromtimestamp(timestamp, kst)
        return dt.timetuple()

    def formatTime(self, record, datefmt=None):
        # Use the custom converter to get the time in KST
        ct = self.converter(record.created)
        if datefmt:
            s = datetime.fromtimestamp(
                record.created, pytz.timezone("Asia/Seoul")
            ).strftime(datefmt)
        else:
            t = datetime.fromtimestamp(record.created, pytz.timezone("Asia/Seoul"))
            s = t.strftime("%Y-%m-%d %H:%M:%S")
        return s


class LoggerSetup:
    def __init__(self, press_name):
        self.logger = self.setup_logging(press_name)

    def setup_logging(self, press_name):
        logger = logging.getLogger(press_name)
        if logger.hasHandlers():
            logger.handlers.clear()  # Remove all handlers associated with the logger

        kst = pytz.timezone("Asia/Seoul")
        today = datetime.now(kst).strftime("%Y-%m-%d")
        log_directory = os.path.join(
            directory_path[press_name], "next-repeater", "logs"
        )
        os.makedirs(log_directory, exist_ok=True)
        log_filename = os.path.join(log_directory, f"news_repeater_{today}.log")

        handler = logging.FileHandler(log_filename)
        handler.setLevel(logging.INFO)

        # Use the KSTFormatter
        formatter = KSTFormatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(handler)

        return logger
