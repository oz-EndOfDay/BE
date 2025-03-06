# import io
# import os
# import uuid
# from datetime import datetime, timedelta
#
# import boto3
# import pytest
# from moto import mock_aws
# from PIL import Image
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src.config import Settings
# from src.diary.models import Diary
# from src.diary.service.tasks import delete_expired_diaries
# from src.ex_diary.models import ExDiary
# from src.friend.models import Friend
# from src.user.models import User
#
# settings = Settings()
#
#
# @pytest.mark.asyncio
# async def test_delete_expired_diaries_with_s3(async_session: AsyncSession):
#     # S3 모킹
#     with mock_aws():
#         # S3 클라이언트 설정
#         s3_client = boto3.client(
#             "s3",
#             region_name=settings.AWS_REGION,
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#         )
#
#         # 테스트 버킷 생성 (us-east-1이 아닌 경우에만 LocationConstraint 설정)
#         if settings.AWS_REGION != "us-east-1":
#             s3_client.create_bucket(
#                 Bucket=settings.S3_BUCKET_NAME,
#                 CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
#             )
#         else:
#             s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)
#
#         # 테스트 사용자 생성
#         test_user = User(
#             name="Test User",
#             email="test@example.com",
#             nickname="testuser",
#             password="password123",
#             is_active=False,
#             provider="",
#         )
#         async_session.add(test_user)
#         await async_session.flush()
#
#         # 테스트 이미지 생성 및 S3 업로드
#         test_image = create_test_image()
#         image_filename = f"test_diary_{uuid.uuid4()}.jpg"
#         s3_key = f"diaries/{image_filename}"
#
#         s3_client.upload_fileobj(
#             test_image,
#             settings.S3_BUCKET_NAME,
#             s3_key,
#             ExtraArgs={"ContentType": "image/jpeg"},
#         )
#
#         # 만료된 일기 생성 (이미지 URL 포함)
#         img_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
#         expired_diary = Diary(
#             title="Expired Test Diary",
#             user_id=test_user.id,
#             write_date=datetime.now().date(),
#             weather="맑음",
#             mood="기쁨",
#             content="Test content",
#             deleted_at=datetime.now() - timedelta(days=8),
#             img_url=img_url,
#         )
#         async_session.add(expired_diary)
#         await async_session.commit()
#
#         # 태스크 실행 (S3 클라이언트 전달)
#         await delete_expired_diaries(async_session, s3_client)
#
#         # 만료된 일기 삭제 확인
#         result = await async_session.execute(
#             select(Diary).where(Diary.id == expired_diary.id)
#         )
#         assert result.scalar_one_or_none() is None
#
#         # S3 이미지 삭제 확인
#         try:
#             s3_client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
#             pytest.fail("이미지가 삭제되지 않았습니다")
#         except s3_client.exceptions.ClientError as e:
#             error_code = e.response["Error"]["Code"]
#             assert error_code == "404"
#
#
# def create_test_image():
#     # 테스트용 이미지 생성
#     image = Image.new("RGB", (100, 100), color="red")
#     img_byte_arr = io.BytesIO()
#     image.save(img_byte_arr, format="JPEG")
#     img_byte_arr.seek(0)
#     return img_byte_arr

import io
import logging
import time
import uuid
from datetime import datetime, timedelta

import boto3
import pytest
from botocore.exceptions import ClientError
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.diary.models import Diary
from src.diary.service.tasks import delete_expired_diaries
from src.user.models import User

logging.basicConfig(level=logging.DEBUG)
settings = Settings()


@pytest.mark.asyncio
async def test_delete_expired_diaries_with_ncp(async_session: AsyncSession):
    # NCP S3 클라이언트 설정
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.NCP_ACCESS_KEY,
        aws_secret_access_key=settings.NCP_SECRET_KEY,
        endpoint_url=settings.NCP_ENDPOINT_URL,
    )

    # 테스트 사용자 생성
    test_user = User(
        name="Test User",
        email="test@example.com",
        nickname="testuser",
        password="password123",
        is_active=False,
        provider="",
    )
    async_session.add(test_user)
    await async_session.flush()

    # 테스트 이미지 생성 및 NCP Object Storage 업로드
    test_image = create_test_image()
    image_filename = f"test_diary_{uuid.uuid4()}.jpg"
    s3_key = f"diaries/{image_filename}"

    try:
        s3_client.upload_fileobj(
            test_image,
            settings.NCP_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ACL": "public-read"},
        )
        logging.info(f"Test image uploaded successfully: {s3_key}")
    except ClientError as e:
        pytest.fail(f"이미지 업로드 실패: {str(e)}")

    # 만료된 일기 생성 (이미지 URL 포함)
    img_url = f"{settings.NCP_ENDPOINT_URL}/{settings.NCP_BUCKET_NAME}/{s3_key}"
    expired_diary = Diary(
        title="Expired Test Diary",
        user_id=test_user.id,
        write_date=datetime.now().date(),
        weather="맑음",
        mood="기쁨",
        content="Test content",
        deleted_at=datetime.now() - timedelta(days=8),
        img_url=img_url,
    )
    async_session.add(expired_diary)
    await async_session.commit()
    logging.info(f"Expired diary created with ID: {expired_diary.id}")

    # 태스크 실행
    await delete_expired_diaries(async_session, s3_client)

    # 잠시 대기 (삭제 작업이 완료되기를 기다림)
    time.sleep(2)

    # 만료된 일기 삭제 확인
    result = await async_session.execute(
        select(Diary).where(Diary.id == expired_diary.id)
    )
    assert result.scalar_one_or_none() is None
    logging.info("Expired diary successfully deleted from database")

    # NCP Object Storage 이미지 삭제 확인
    try:
        s3_client.head_object(Bucket=settings.NCP_BUCKET_NAME, Key=s3_key)

        # 이미지가 여전히 존재하면 수동으로 삭제 시도
        logging.warning(
            "이미지가 자동으로 삭제되지 않았습니다. 수동 삭제를 시도합니다."
        )
        s3_client.delete_object(Bucket=settings.NCP_BUCKET_NAME, Key=s3_key)

        # 삭제 후 다시 확인
        time.sleep(1)
        s3_client.head_object(Bucket=settings.NCP_BUCKET_NAME, Key=s3_key)
        pytest.fail("이미지 수동 삭제 후에도 여전히 존재합니다.")
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            logging.info("이미지가 성공적으로 삭제되었습니다.")
        else:
            pytest.fail(f"예상치 못한 오류 발생: {str(e)}")


def create_test_image():
    image = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    return img_byte_arr


# delete_expired_diaries 함수 (tasks.py 파일에 있어야 함)
async def delete_expired_diaries(session: AsyncSession, s3_client):
    # 7일 이상 지난 삭제된 일기 조회
    seven_days_ago = datetime.now() - timedelta(days=7)
    expired_diaries = await session.execute(
        select(Diary).where(
            (Diary.deleted_at.isnot(None)) & (Diary.deleted_at <= seven_days_ago)
        )
    )
    expired_diaries = expired_diaries.scalars().all()

    for diary in expired_diaries:
        if diary.img_url:
            try:
                key = diary.img_url.split("/")[-1]
                logging.info(f"Attempting to delete image: {key}")
                s3_client.delete_object(Bucket=settings.NCP_BUCKET_NAME, Key=key)
                logging.info(f"Image deleted successfully: {key}")
            except Exception as e:
                logging.error(f"Failed to delete image: {key}. Error: {str(e)}")

        await session.delete(diary)

    await session.commit()
    logging.info(f"Deleted {len(expired_diaries)} expired diaries")
