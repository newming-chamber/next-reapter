from ftplib import FTP
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import boto3
from shutil import copy2
from datetime import datetime
import pytz
import logging

load_dotenv()
env = os.environ
directory_path = {
    "hi": "/home/hankookilbo",  # 한국일보
    "mk": "/home/mk",  # 매일경제
    "fn": "/home/fnnews",  # 파이낸셜
    "hn": "/home/hani",  # 한겨례
    "ja": "/home/joongang",  # 중앙일보
    "kh": "/home/khan",  # 경향신문
    "hk": "/home/hankyung",  # 한국경제
}
base_path = directory_path
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename=f"{directory_path[env['PRESS_NAME']]}/next-repeater/news_repeater.log",
)
logger = logging.getLogger(__name__)

kst = pytz.timezone("Asia/Seoul")
s3 = boto3.client(
    "s3",
    region_name=env.get("AWS_REGION", "ap-northeast-2"),
    aws_access_key_id=env["ACCESS_KEY"],
    aws_secret_access_key=env["SECRET_KEY"],
)


# def download_file(ftp, filename, filepath):
#     if not os.path.exists(filepath):
#         try:
#             os.makedirs(os.path.dirname(filepath), exist_ok=True)
#             with open(filepath, "wb") as f:
#                 ftp.retrbinary("RETR " + filename, f.write)
#             print("File", filename, "downloaded")
#         except Exception as e:
#             print("File", filename, "error:", e)


# def sync_press():
#     now = datetime.now() + timedelta(hours=9)
#     fifteen_days_ago = now - timedelta(days=15)

#     ftp = FTP()
#     ftp.connect("210.179.172.10", 8023)
#     ftp.login("griptoday", "vUTg1^d8VE")
#     print(ftp.getwelcome())

#     files = ftp.nlst()
#     for filename in files:
#         try:
#             publish_time = filename.split("_")[1]
#             file_time = datetime.strptime(publish_time, "%Y%m%d%H%M%S")

#             if file_time > fifteen_days_ago:
#                 filepath = "/home/mk/" + filename
#                 download_file(ftp, filename, filepath)
#             else:
#                 filepath = "/home/mk/" + filename
#                 if os.path.exists(filepath):
#                     os.remove(filepath)
#                     print("File", filename, "deleted")
#         except Exception as e:
#             print("File", filename, "error:", e)

#     ftp.close()


def s3_object_exists(object_name):
    bucket = env["S3_BUCKET"]
    try:
        s3.head_object(Bucket=bucket, Key=object_name)
        return True
    except Exception as e:
        return False


def upload_file_to_s3(file_name, object_name):
    bucket = env["S3_BUCKET"]
    s3.upload_file(file_name, bucket, object_name)


def remove_old_files():
    result = {"delete": 0}
    process_directory = os.path.join(os.getcwd(), "process_files")
    now = datetime.now(kst)
    threshold_time = now - timedelta(days=1)

    for filename in os.listdir(process_directory):
        file_path = os.path.join(process_directory, filename)
        file_mod_time = datetime.fromtimestamp(os.stat(file_path).st_mtime, kst)

        if file_mod_time < threshold_time:
            try:
                os.remove(file_path)
                logger.info(f"REMOVE {file_path} (modified at {file_mod_time})")
                result["delete"] += 1

            except Exception as e:
                logger.error(f"Error removing file {file_path}: {e}")
    return result


def process_files(press_name):
    result = {"copy": 0, "upload": 0, "delete": 0}
    file_direcotry = directory_path[press_name] if env["ENV"] else os.getcwd()
    file_list = os.listdir(file_direcotry)
    process_directory = os.path.join(os.getcwd(), "process_files")
    os.makedirs(process_directory, exist_ok=True)
    if press_name == "mk":
        # mk로 시작하는 파일을 선택
        file_list = [i for i in file_list if i.startswith("mk")]
    else:
        # .xml로 끝나는 파일을 선택
        file_list = [i for i in file_list if i.endswith(".xml")]

    for filename in file_list:
        try:
            source_path = os.path.join(file_direcotry, filename)
            destination_path = os.path.join(process_directory, filename)

            process_file_exist = os.path.exists(destination_path)

            modifited_time = os.stat(source_path).st_mtime
            now = datetime.now(kst).timestamp()
            if not process_file_exist:
                # process 로 이동
                copy2(source_path, destination_path)

                logger.info(f"COPY {source_path} -> {destination_path}")
                result["copy"] += 1

                # s3 업로드
                if now - modifited_time < 60 * 5:
                    object_name = f"origin_news/{press_name}/{filename}"
                    upload_file_to_s3(os.path.join(destination_path), object_name)

                    for_stage = f"stage_news/{press_name}/{filename}"
                    upload_file_to_s3(os.path.join(destination_path), for_stage)

                    logger.info(f"UPLOAD {filename} {object_name}")
                    result["upload"] += 1

            elif process_file_exist:
                os.remove(source_path)
                result["delete"] += 1
                logger.info(f"DELETE {source_path}")

        except Exception as e:
            logger.error(f"Error: {press_name} {filename} {e}")

    return result


def main():
    press_name = env["PRESS_NAME"]
    need_sync_press = ["mk", "fn"]
    # if press_name in need_sync_press:
    #     sync_press()
    logger.info(f"Start {press_name} Repeater")
    process_result = process_files(press_name)
    remove_result = remove_old_files()
    total_delete = process_result["delete"] + remove_result["delete"]

    # 최종 결과를 병합합니다
    combined_result = {
        "copy": process_result["copy"],
        "upload": process_result["upload"],
        "delete": total_delete,
    }
    print(combined_result)


# Run the main function
main()
