from typing import Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.diary.models import Diary


class DiaryReqository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, diary: Diary) -> None:
        self.session.add(diary)
        await self.session.commit()

    async def get_diary_list(self, user_id: int) -> Sequence[Diary] | None:
        query = (
            select(Diary)
            .where(Diary.user_id == user_id)
            .order_by(Diary.created_at.desc())
        )
        result = await self.session.execute(query)
        diaries = result.scalars().all()
        return diaries or None
