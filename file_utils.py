import os
from shutil import copy2
from datetime import datetime, timedelta
import pytz
from .logger import LoggerSetup
from .s3_utils import S3Manager
from .config import directory_path


class FileManager:
    def __init__(self, press_name):
        self.press_name = press_name
        self.directory_path = directory_path[press_name]
        self.logger = LoggerSetup(press_name).logger
        self.s3_manager = S3Manager()

    def download_file(self, ftp, filename, filepath):
        if not os.path.exists(filepath):
            try:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "wb") as f:
                    ftp.retrbinary("RETR " + filename, f.write)
                self.logger.info(f"File {filename} downloaded")
            except Exception as e:
                self.logger.info(f"File {filename} error: {e}")

    def remove_old_files(self, process_directory):
        result = {"delete": 0}
        process_directory = os.path.join(os.getcwd(), "process_files")
        kst = pytz.timezone("Asia/Seoul")
        now = datetime.now(kst)
        threshold_time = now - timedelta(days=1)

        for filename in os.listdir(process_directory):
            file_path = os.path.join(process_directory, filename)
            file_mod_time = datetime.fromtimestamp(os.stat(file_path).st_mtime, kst)

            if file_mod_time < threshold_time:
                try:
                    os.remove(file_path)
                    self.logger.info(
                        f"REMOVE {file_path} (modified at {file_mod_time})"
                    )
                    result["delete"] += 1
                except Exception as e:
                    self.logger.error(f"Error removing file {file_path}: {e}")
        return result

    def process_files(self):
        result = {"copy": 0, "upload": 0, "delete": 0}
        file_list = os.listdir(self.directory_path)
        process_directory = os.path.join(os.getcwd(), "process_files")
        os.makedirs(process_directory, exist_ok=True)

        if self.press_name == "mk":
            file_list = [i for i in file_list if i.startswith("mk")]
        else:
            file_list = [i for i in file_list if i.endswith(".xml")]

        for filename in file_list:
            try:
                source_path = os.path.join(self.directory_path, filename)
                destination_path = os.path.join(process_directory, filename)

                process_file_exist = os.path.exists(destination_path)

                copy2(source_path, destination_path)
                if not process_file_exist:
                    self.parsing_news("prod", filename, destination_path)
                    self.parsing_news("stage", filename, destination_path)

                    result["upload"] += 1
                    os.remove(destination_path)
                    result["delete"] += 1
                    self.logger.info(f"DELETE process path {destination_path}")

                elif process_file_exist:
                    os.remove(source_path)
                    result["delete"] += 1
                    self.logger.info(f"DELETE origin path {source_path}")

            except Exception as e:
                self.logger.error(f"Error: {self.press_name} {filename} {e}")

        return result

    def parsing_news(self, env, filename, destination_path):
        object_name = (
            f"origin_news/{self.press_name}/{filename}"
            if env == "prod"
            else f"stage_news/{self.press_name}/{filename}"
        )
        self.s3_manager.upload_file_to_s3(os.path.join(destination_path), object_name)
        self.logger.info(f"UPLOAD {filename} {object_name}")
