from ftplib import FTP
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import boto3
from shutil import copy2
from datetime import datetime
import pytz

load_dotenv()
kst = pytz.timezone("Asia/Seoul")
env = os.environ
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
    try:
        s3.upload_file(file_name, bucket, object_name)
        print("File", file_name, "uploaded to s3 as", object_name)
    except Exception as e:
        print(e)
        return False
    return True


def process_files(press_name):
    file_direcotry = f"/home/{press_name}" if env["ENV"] else os.getcwd()
    file_list = os.listdir(file_direcotry)
    process_directory = os.path.join(file_direcotry, "process")
    os.makedirs(process_directory, exist_ok=True)
    if press_name == "mk":
        # mk로 시작하는 파일을 선택
        file_list = [i for i in file_list if i.startswith("mk")]
    else:
        # .xml로 끝나는 파일을 선택
        file_list = [i for i in file_list if i.endswith(".xml")]

    for filename in file_list:
        source_path = os.path.join(file_direcotry, filename)
        destination_path = os.path.join(process_directory, filename)

        origin_file_exist = os.path.exists(destination_path)

        if not origin_file_exist:
            copy2(source_path, destination_path)
            print("File", filename, "copied")
            modifited_time = os.stat(source_path).st_mtime
            now = datetime.now(kst).timestamp()
            print(now)
            if (now - modifited_time) < 60 * 10:
                object_name = f"origin_news/{press_name}/{filename}"
                upload_file_to_s3(os.path.join(destination_path), object_name)


def main():
    press_name = env["PRESS_NAME"]
    need_sync_press = ["mk", "fn"]
    # if press_name in need_sync_press:
    #     sync_press()
    process_files(press_name)


# Run the main function
main()
