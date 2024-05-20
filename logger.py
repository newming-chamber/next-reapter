import logging
import os
from datetime import datetime
import pytz
from .config import directory_path, env


class LoggerSetup:
    def __init__(self, press_name):
        self.logger = self.setup_logging(press_name)

    def setup_logging(self, press_name):
        kst = pytz.timezone("Asia/Seoul")
        today = datetime.now(kst).strftime("%Y-%m-%d")
        log_directory = os.path.join(
            directory_path[press_name], "next-repeater", "logs"
        )
        os.makedirs(log_directory, exist_ok=True)
        log_filename = os.path.join(log_directory, f"news_repeater_{today}.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            filename=log_filename,
        )
        return logging.getLogger(press_name)
