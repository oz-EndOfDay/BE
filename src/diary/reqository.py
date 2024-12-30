from fastapi import Depends
from sqlalchemy.orm import Session

from src.config.database.connection import get_async_session
from src.diary.models import Diary


class DiaryReqository:
    def __init__(self, session: Session = Depends(get_async_session)):
        self.session = session

    async def save(self, diary: Diary):
        self.session.add(diary)
        await self.session.commit()