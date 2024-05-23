import os
from shutil import copy2
from ftplib import FTP
from datetime import datetime
import pytz
from .logger import LoggerSetup
from .config import *


class FTPManager:
    def __init__(self, press_name, file_manager):
        self.ftp_host = env["FTP_HOST"]
        self.ftp_port = int(env["FTP_PORT"])
        self.ftp_id = env["FTP_ID"]
        self.ftp_pw = env["FTP_PW"]
        self.press_name = env["PRESS_NAME"]
        self.file_manager = file_manager
        self.logger = LoggerSetup(press_name).logger

    def sync_press(self):
        download_list = []
        kst = pytz.timezone("Asia/Seoul")
        ftp = FTP()
        ftp.connect(self.ftp_host, self.ftp_port)
        ftp.login(self.ftp_id, self.ftp_pw)
        self.logger.info(ftp.getwelcome())

        files = ftp.nlst()
        self.logger.info(f"FTP File Count : {len(files)}")
        for filename in files:
            try:
                if self.press_name == "mk":
                    if not filename.startswith("mk"):
                        continue

                    publish_time = filename.split("_")[1]
                    file_time = datetime.strptime(publish_time, "%Y%m%d%H%M%S")
                    file_time = kst.localize(file_time)
                else:
                    if not filename.endswith(".xml") and not (
                        self.press_name == "fn" and filename.endswith(".xml.tmp")
                    ):
                        continue
                    modified_time = ftp.sendcmd(f"MDTM {filename}")[4:]
                    file_time = datetime.strptime(
                        modified_time, "%Y%m%d%H%M%S"
                    ) + timedelta(hours=9)
                    file_time = kst.localize(file_time)

                filepath = os.path.join(
                    self.file_manager.directory_path, "origin_files", filename
                )
                is_downloaded = os.path.exists(filepath)
                if not is_downloaded and file_time > FTP_DOWNLOAD_THRESS_HOLD:
                    self.file_manager.download_file(ftp, filename, filepath)
                    copy2(
                        src=filepath,
                        dst=os.path.join(self.file_manager.directory_path, filename),
                    )
                    download_list.append(filename)

                # if file_time < FTP_DELETED_THRESS_HOLD:
                #     ftp.delete(filename)
                #     self.logger.info(f"FTP File {filename} deleted")

            except Exception as e:
                self.logger.info(f"File {filename} error: {e}")

        ftp.close()
        return download_list
