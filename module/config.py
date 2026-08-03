import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pytz


load_dotenv()
env = os.environ

directory_path = {
    "hi": "/home/hankookilbo",
    "mk": "/home/mk",
    "fn": "/home/fnnews",
    "hn": "/home/hani",
    "ja": "/home/joongang",
    "kh": "/home/khan",
    "hk": "/home/hankyung",
    "sc": "/home/sportschosun/origin_files",
}

kst = pytz.timezone("Asia/Seoul")
now = datetime.now(kst)

FTP_DOWNLOAD_THRESS_HOLD = now - timedelta(days=7 * 2)
FTP_DELETED_THRESS_HOLD = now - timedelta(days=30 * 6)
UPLOAD_THRESS_HOLD = now - timedelta(minutes=30)
FILE_DELETE_THRESS_HOLD = now - timedelta(days=3)

ORIGIN_FILE_DELETE = True

# 한 번의 실행에서 처리할 최대 파일 수.
# 크론이 1분 주기이므로 누적분(sc 이미지 15만여 건)을 한 번에 처리하면 실행이 겹친다.
PROCESS_BATCH_LIMIT = 200
