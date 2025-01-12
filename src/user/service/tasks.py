import logging
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError
from celery import shared_task
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.config.database.connection import AsyncSessionFactory
from src.user.models import User

settings = Settings()
logger = logging.getLogger(__name__)

async def delete_expired_users_task() -> None:
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    async with AsyncSessionFactory() as session:
        async with session.begin():
            await delete_expired_users(session, s3_client)

@shared_task(name="tasks.delete_expired_users")  # type: ignore
async def delete_expired_users(
    session: AsyncSession, s3_client: boto3.client
) -> None:
    threshold_date = datetime.now() - timedelta(days=7)

    # 삭제 예정 사용자 먼저 조회
    expired_users = await session.execute(
        select(User).where(
            User.deleted_at.isnot(None), User.deleted_at <= threshold_date
        )
    )

    # S3에서 프로필 이미지 대량 삭제
    for user in expired_users.scalars():
        if user.img_url:
            try:
                # URL에서 S3 키 추출
                s3_key = user.img_url.split(
                    f"{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/"
                )[1]

                s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
            except (ClientError, IndexError) as e:
                logger.error(f"S3 프로필 이미지 삭제 실패: {user.id}, {str(e)}")

    # 데이터베이스에서 대량 삭제
    await session.execute(
        delete(User).where(
            User.deleted_at.isnot(None), User.deleted_at <= threshold_date
        )
    )
    await session.commit()
