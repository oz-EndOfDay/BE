from typing import Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.connection import get_async_session
from diary.models import Diary


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
            .where(Diary.deleted_at.is_(None))  # 삭제되지 않은 일기만 검색
            .order_by(Diary.created_at.desc())
        )
        result = await self.session.execute(query)
        diaries = result.scalars().all()
        return diaries or None

    async def get_deleted_diary_list(self, user_id: int) -> Sequence[Diary] | None:
        query = (
            select(Diary)
            .where(Diary.user_id == user_id)
            .where(Diary.deleted_at.is_not(None))  # 삭제 예정인 일기만 검색
            .order_by(Diary.deleted_at.desc())
        )
        result = await self.session.execute(query)
        diaries = result.scalars().all()
        return diaries or None

    async def get_diary_detail(self, diary_id: int) -> Diary:
        query = (
            select(Diary).where(Diary.id == diary_id)
            # .where(Diary.deleted_at.is_(None))      # 삭제되지 않은 일기만 검색
        )
        result = await self.session.execute(query)
        diary = result.scalars().first()
        return diary

    async def delete(self, diary: Diary) -> None:
        await diary.soft_delete(self.session)

    async def restore_diary(self, diary_id: int) -> Diary | None:
        query = select(Diary).where(Diary.id == diary_id)
        result = await self.session.execute(query)
        diary = result.scalars().first()

        if diary and diary.deleted_at:
            await diary.restore(self.session)
            return diary
        return None
