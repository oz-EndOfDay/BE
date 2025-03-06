import logging
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError
from celery import shared_task
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.config.database.connection import AsyncSessionFactory
from src.diary.models import Diary

settings = Settings()
logger = logging.getLogger(__name__)


async def delete_expired_diaries_task() -> None:
    # s3_client = boto3.client(
    #     "s3",
    #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    #     region_name=settings.AWS_REGION,
    # )
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.NCP_ACCESS_KEY,
        aws_secret_access_key=settings.NCP_SECRET_KEY,
        endpoint_url=settings.NCP_ENDPOINT_URL,
    )

    async with AsyncSessionFactory() as session:
        async with session.begin():
            await delete_expired_diaries(session, s3_client)


@shared_task(name="tasks.delete_expired_diaries")  # type: ignore
async def delete_expired_diaries(
    session: AsyncSession, s3_client: boto3.client
) -> None:
    seven_days_ago = datetime.now() - timedelta(days=7)

    logger.info("Deleting expired diaries started...")

    # 삭제 예정 일기 먼저 조회
    expired_diaries = await session.execute(
        select(Diary).where(
            Diary.deleted_at.isnot(None), Diary.deleted_at <= seven_days_ago
        )
    )

    # S3에서 이미지 대량 삭제
    for diary in expired_diaries.scalars():
        if diary.img_url:
            try:
                s3_key = diary.img_url.split(
                    # f"{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/"
                    f"{settings.NCP_ENDPOINT_URL}/{settings.NCP_BUCKET_NAME}/"
                )[1]

                s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
            except ClientError as e:
                # 로깅 추천
                logger.error(f"S3 이미지 삭제 실패: {diary.id}, {str(e)}")
    logger.info(f"Deleted S3 image for user/diary {diary.id}")

    # 데이터베이스에서 대량 삭제
    await session.execute(
        delete(Diary).where(
            Diary.deleted_at.isnot(None), Diary.deleted_at <= seven_days_ago
        )
    )
    await session.commit()
    logger.info("Expired diaries deletion completed.")
