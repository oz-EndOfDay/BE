from datetime import datetime

from boto3 import client
from fastapi import UploadFile

from src.config import Settings

settings = Settings()

s3_client = client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)


async def image_upload(file: UploadFile, user_id: int) -> None:
    bucket = settings.S3_BUCKET_NAME
    image_filename = f"profile_{user_id}_{datetime.now()}"
    s3_key = f"profiles/{image_filename}"
    await s3_client.upload_fileobj(
        file, bucket, s3_key, ExtraArgs={"ContentType": "image/jpeg"}
    )
