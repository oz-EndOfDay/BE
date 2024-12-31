from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config.database.connection import get_async_session
from src.diary.models import Diary


class DiaryReqository:
    def __init__(self, session: Session = Depends(get_async_session)):
        self.session = session

    async def save(self, diary: Diary) -> None:
        self.session.add(diary)
        await self.session.commit()  # type: ignore

    async def get_diary_list(self, user_id: int) -> list[Diary] | None:
        query = select(Diary).where(Diary.user_id == user_id).order_by(Diary.created_at.desc())
        result = await self.session.execute(query)
        return result.scalars().all()
