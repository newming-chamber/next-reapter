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
        delete_count = 0
        for filename in files:
            if len(download_list) > 100:
                self.logger.info("Downloaded file count is over 100")
                break
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

                filepath = os.path.join(self.file_manager.directory_path, filename)
                is_downloaded = os.path.exists(filepath)
                # process_file_path = os.path.join(
                #     self.file_manager.directory_path, "origin_files", filename
                # )
                # is_processed = os.path.exists(process_file_path)
                if file_time > FTP_DOWNLOAD_THRESS_HOLD:
                    if not is_downloaded:
                        self.file_manager.download_file(ftp, filename, filepath)
                        download_list.append(filename)
                    else:
                        delete_count += 1
                        # ftp.delete(filename)

                # if file_time < FTP_DELETED_THRESS_HOLD:
                #     ftp.delete(filename)
                #     self.logger.info(f"FTP File {filename} deleted")

            except Exception as e:
                self.logger.info(f"File {filename} error: {e}")
        self.logger.info(f"Delete Count : {delete_count}")
        ftp.close()
        return download_list
