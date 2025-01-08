import boto3
from botocore.exceptions import ClientError
from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.config.database.connection import get_async_session
from src.ex_diary.models import ExDiary

settings = Settings()


class ExDiaryRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, ex_diary: ExDiary) -> None:
        self.session.add(ex_diary)
        await self.session.commit()

    async def get_ex_diary_list(self, friend_id: int) -> list[ExDiary]:

        query = (
            select(ExDiary)
            .where(ExDiary.friend_id == friend_id)  # 친구와 작성한 교환 일기 전부 검색
            .order_by(ExDiary.created_at.desc())
        )
        result = await self.session.execute(query)
        ex_diaries = result.scalars().all()

        return list(ex_diaries)

    async def get_ex_diary_detail(
        self, friend_id: int, ex_diary_id: int
    ) -> ExDiary | None:
        query = select(ExDiary).where(
            ExDiary.friend_id == friend_id, ExDiary.id == ex_diary_id
        )
        result = await self.session.execute(query)
        ex_diary = result.scalar_one_or_none()

        return ex_diary

    async def delete_ex_diary(
        self, user_id: int, friend_id: int, ex_diary_id: int
    ) -> None:
        # 삭제할 교환일기 조회
        query = select(ExDiary).where(
            ExDiary.friend_id == friend_id, ExDiary.id == ex_diary_id
        )
        result = await self.session.execute(query)
        ex_diary = result.scalar_one_or_none()

        # 교환일기가 존재하지 않으면 예외 발생
        if not ex_diary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "message": "삭제할 교환일기를 찾을 수 없습니다.",
                    "status": "fail",
                },
            )

        # 현재 로그인된 사용자의 user_id와 일기 작성자의 user_id가 동일한지 검증
        if ex_diary.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "message": "삭제 권한이 없습니다.",
                    "status": "fail",
                },
            )

        # S3 이미지 삭제 로직 추가
        if ex_diary.img_url:
            s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )

            # S3 키 추출 (URL에서 버킷 이름 제외한 키 부분 추출)
            s3_key = ex_diary.img_url.split(
                f"{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/"
            )[1]

            try:
                # S3에서 이미지 삭제
                s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
            except ClientError as e:
                # S3 삭제 실패해도 일기 삭제 진행
                print(f"S3 이미지 삭제 실패: {str(e)}")

        # 교환일기 삭제 및 커밋
        await self.session.delete(ex_diary)
        await self.session.commit()
