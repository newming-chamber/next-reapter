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
}

kst = pytz.timezone("Asia/Seoul")
now = datetime.now(kst)

FTP_DOWNLOAD_THRESS_HOLD = now - timedelta(hours=10)
FTP_DELETED_THRESS_HOLD = now - timedelta(days=30 * 6)
UPLOAD_THRESS_HOLD = now - timedelta(minutes=10)
FILE_DELETE_THRESS_HOLD = now - timedelta(days=1)
