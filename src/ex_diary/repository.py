from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.ex_diary.models import ExDiary


class ExDiaryRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, ex_diary: ExDiary) -> None:
        self.session.add(ex_diary)
        await self.session.commit()
