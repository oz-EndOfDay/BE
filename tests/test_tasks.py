import io
import os
import uuid
from datetime import datetime, timedelta

import boto3
import pytest
from moto import mock_aws
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.diary.models import Diary
from src.diary.service.tasks import delete_expired_diaries
from src.ex_diary.models import ExDiary
from src.friend.models import Friend
from src.user.models import User

settings = Settings()


@pytest.mark.asyncio
async def test_delete_expired_diaries_with_s3(async_session: AsyncSession):
    # S3 모킹
    with mock_aws():
        # S3 클라이언트 설정
        s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

        # 테스트 버킷 생성 (us-east-1이 아닌 경우에만 LocationConstraint 설정)
        if settings.AWS_REGION != "us-east-1":
            s3_client.create_bucket(
                Bucket=settings.S3_BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": settings.AWS_REGION},
            )
        else:
            s3_client.create_bucket(Bucket=settings.S3_BUCKET_NAME)

        # 테스트 사용자 생성
        test_user = User(
            name="Test User",
            email="test@example.com",
            nickname="testuser",
            password="password123",
        )
        async_session.add(test_user)
        await async_session.flush()

        # 테스트 이미지 생성 및 S3 업로드
        test_image = create_test_image()
        image_filename = f"test_diary_{uuid.uuid4()}.jpg"
        s3_key = f"diaries/{image_filename}"

        s3_client.upload_fileobj(
            test_image,
            settings.S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )

        # 만료된 일기 생성 (이미지 URL 포함)
        img_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
        expired_diary = Diary(
            title="Expired Test Diary",
            user_id=test_user.id,
            write_date=datetime.now().date(),
            content="Test content",
            deleted_at=datetime.now() - timedelta(days=8),
            img_url=img_url,
        )
        async_session.add(expired_diary)
        await async_session.commit()

        # 태스크 실행 (S3 클라이언트 전달)
        await delete_expired_diaries(async_session, s3_client)

        # 만료된 일기 삭제 확인
        result = await async_session.execute(
            select(Diary).where(Diary.id == expired_diary.id)
        )
        assert result.scalar_one_or_none() is None

        # S3 이미지 삭제 확인
        try:
            s3_client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
            pytest.fail("이미지가 삭제되지 않았습니다")
        except s3_client.exceptions.ClientError as e:
            error_code = e.response["Error"]["Code"]
            assert error_code == "404"


def create_test_image():
    # 테스트용 이미지 생성
    image = Image.new("RGB", (100, 100), color="red")
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    return img_byte_arr
