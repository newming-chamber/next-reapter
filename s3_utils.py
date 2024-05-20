import boto3
from .config import env


class S3Manager:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            region_name=env.get("AWS_REGION", "ap-northeast-2"),
            aws_access_key_id=env["ACCESS_KEY"],
            aws_secret_access_key=env["SECRET_KEY"],
        )
        self.bucket = env["S3_BUCKET"]

    def s3_object_exists(self, object_name):
        try:
            self.s3.head_object(Bucket=self.bucket, Key=object_name)
            return True
        except Exception:
            return False

    def upload_file_to_s3(self, file_name, object_name):
        self.s3.upload_file(file_name, self.bucket, object_name)
