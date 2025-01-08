from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.ex_diary.models import ExDiary


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
