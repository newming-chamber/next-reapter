import os
from shutil import copy2
from datetime import datetime
import pytz
from .logger import LoggerSetup
from .s3_utils import S3Manager
from .config import (
    directory_path,
    UPLOAD_THRESS_HOLD,
    ORIGIN_FILE_DELETE,
    FILE_DELETE_THRESS_HOLD,
    PROCESS_BATCH_LIMIT,
)


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
                self.logger.info(f"DOWNLOAD {filename}")
            except Exception as e:
                self.logger.info(f"File {filename} error: {e}")

    def remove_old_files(self, extensions=None):
        """백업 폴더(origin_files)에서 보관 기간이 지난 파일을 회수한다.

        extensions: 대상 확장자 튜플. None이면 전체가 대상.
        S3에 원본이 존재하는 것만 삭제한다.
        """
        delete_result = []
        backup_directory = os.path.join(self.directory_path, "origin_files")
        if not os.path.isdir(backup_directory):
            return delete_result

        for filename in os.listdir(backup_directory):
            file_path = os.path.join(backup_directory, filename)

            # sc는 입력 경로 자체가 origin_files라 백업이 중첩되어 디렉토리가 섞인다
            if not os.path.isfile(file_path):
                continue
            if extensions and not filename.lower().endswith(extensions):
                continue

            file_mod_time = self.get_file_mod_time(file_path)
            if file_mod_time >= FILE_DELETE_THRESS_HOLD:
                continue

            # 업로드가 조용히 실패한 경우 로컬 원본까지 잃지 않도록 S3 존재를 확인한다
            object_name = self.build_object_name(filename, "prod")
            if not self.s3_manager.s3_object_exists(object_name):
                self.logger.error(f"SKIP DELETE not found on S3 {object_name}")
                continue

            try:
                os.remove(file_path)
                self.logger.info(f"REMOVE {file_path} modified at {file_mod_time}")
                delete_result.append(filename)
            except Exception as e:
                self.logger.error(f"Error removing file {file_path}: {e}")
        return delete_result

    def process_files(self):
        upload_list = []
        file_list = os.listdir(self.directory_path)
        process_directory = os.path.join(os.getcwd(), "process_files")
        os.makedirs(process_directory, exist_ok=True)

        if self.press_name == "mk":
            file_list = [i for i in file_list if i.startswith("mk")]
            file_list.sort(key=lambda x: x.split("_")[1])
        elif self.press_name == "fn":
            file_list = [
                i for i in file_list if i.endswith(".xml") or i.endswith(".xml.tmp")
            ]
            file_list.sort(key=lambda x: (x.endswith(".tmp"), x))
        elif self.press_name == "sc":
            # 스포츠조선은 기사(.xml)와 본문 이미지(.jpg)가 함께 전송된다
            file_list = [
                i for i in file_list if i.endswith(".xml") or i.lower().endswith(".jpg")
            ]
        else:
            file_list = [i for i in file_list if i.endswith(".xml")]

        processed = 0
        for filename in file_list:
            if processed >= PROCESS_BATCH_LIMIT:
                self.logger.info(
                    f"BATCH LIMIT {PROCESS_BATCH_LIMIT} reached, "
                    f"remaining {len(file_list) - processed}"
                )
                break
            processed += 1

            initial_size = os.path.getsize(os.path.join(self.directory_path, filename))
            if initial_size == 0:
                self.logger.info(f"EMPTY file {filename}")
                continue
            try:
                source_path = os.path.join(self.directory_path, filename)
                destination_path = os.path.join(process_directory, filename)

                copy2(source_path, destination_path)
                self.logger.info(f"COPY process path {filename}")
                # file_mod_time = self.get_file_mod_time(source_path)

                # is_procceed = os.path.exists(
                #     os.path.join(self.directory_path, "origin_files", filename)
                # )
                # if file_mod_time > UPLOAD_THRESS_HOLD:
                self.parsing_news("prod", filename, destination_path)
                # 이미지는 아카이브 목적이므로 stage 중복 업로드를 하지 않는다
                if not filename.lower().endswith(".jpg"):
                    self.parsing_news("stage", filename, destination_path)
                upload_list.append(filename)

                os.remove(destination_path)
                self.logger.info(f"DELETE process path {destination_path}")
                self.backup_files(filename)

                if ORIGIN_FILE_DELETE:
                    os.remove(source_path)
                    self.logger.info(f"DELETE origin path {source_path}")

                check_size = os.path.getsize(
                    os.path.join(self.directory_path, "origin_files", filename)
                )

                if check_size != initial_size:
                    self.logger.error(
                        f"Size changed {filename} {initial_size} => {check_size}"
                    )
                    self.rollback_files(filename)

            except Exception as e:
                self.logger.error(f"Error: {self.press_name} {filename} {e}")

        return upload_list

    def build_object_name(self, filename, env):
        # 이미지는 origin_news/{press}/images/ 하위에 둔다.
        # PROD_PRESS_SC 이벤트 알림의 접미사(.xml) 필터에 걸리지 않아 소비자로 유입되지 않는다.
        if filename.lower().endswith(".jpg"):
            return f"origin_news/{self.press_name}/images/{filename}"
        return (
            f"origin_news/{self.press_name}/{filename}"
            if env == "prod"
            else f"stage_news/{self.press_name}/{filename}"
        )

    def parsing_news(self, env, filename, destination_path):
        # if self.press_name == "fn":
        # filename = filename.replace(".tmp", "")
        object_name = self.build_object_name(filename, env)
        self.s3_manager.upload_file_to_s3(os.path.join(destination_path), object_name)
        self.logger.info(f"UPLOAD {filename} {object_name}")

    def get_file_mod_time(self, file_path):
        if self.press_name == "mk":
            publish_time = file_path.split("/").pop().split("_")[1]
            publish_time = datetime.strptime(publish_time, "%Y%m%d%H%M%S")
            return pytz.timezone("Asia/Seoul").localize(publish_time)
        else:
            return datetime.fromtimestamp(
                os.stat(file_path).st_mtime, tz=pytz.timezone("Asia/Seoul")
            )

    def backup_files(self, filename):
        origin_path = os.path.join(self.directory_path, filename)
        backup_path = os.path.join(self.directory_path, "origin_files")

        # Ensure the backup directory exists
        os.makedirs(backup_path, exist_ok=True)
        backup_path = os.path.join(backup_path, filename)

        copy2(origin_path, backup_path)
        self.logger.info(f"BACKUP {origin_path} => {backup_path}")

    def rollback_files(self, filename):
        origin_path = os.path.join(self.directory_path, filename)
        backup_path = os.path.join(self.directory_path, "origin_files", filename)

        copy2(backup_path, origin_path)
        self.logger.info(f"ROLLBACK {backup_path} => {origin_path}")
