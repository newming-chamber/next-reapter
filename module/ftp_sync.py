import os
from ftplib import FTP
from datetime import datetime, timedelta
import pytz
from .logger import LoggerSetup
from .config import directory_path, env
from .file_utils import FileManager


class FTPManager:
    def __init__(self, press_name, file_manager):
        self.ftp_host = env["FTP_HOST"]
        self.ftp_port = int(env["FTP_PORT"])
        self.ftp_id = env["FTP_ID"]
        self.ftp_pw = env["FTP_PW"]
        self.file_manager = file_manager
        self.logger = LoggerSetup(press_name).logger

    def sync_press(self):
        kst = pytz.timezone("Asia/Seoul")
        now = datetime.now(kst)
        threshold_time = now - timedelta(days=1)

        ftp = FTP()
        ftp.connect(self.ftp_host, self.ftp_port)
        ftp.login(self.ftp_id, self.ftp_pw)
        self.logger.info(ftp.getwelcome())

        files = ftp.nlst()
        for filename in files:
            try:
                publish_time = filename.split("_")[1]
                file_time = datetime.strptime(publish_time, "%Y%m%d%H%M%S")
                filepath = os.path.join(
                    self.file_manager.directory_path, "origin_files", filename
                )
                if not os.path.exists(filepath) and file_time > threshold_time:
                    self.file_manager.download_file(ftp, filename, filepath)
            except Exception as e:
                self.logger.info(f"File {filename} error: {e}")

        ftp.close()
