from typing import Optional, Sequence

from fastapi import Depends
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import extract, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.connection import get_async_session
from diary.models import Diary


class DiaryRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def save(self, diary: Diary) -> None:
        self.session.add(diary)
        await self.session.commit()

    # async def get_diary_list(self, user_id: int) -> Sequence[Diary] | None:
    #     query = (
    #         select(Diary)
    #         .where(Diary.user_id == user_id)
    #         .where(Diary.deleted_at.is_(None))  # 삭제되지 않은 일기만 검색
    #         .order_by(Diary.created_at.desc())
    #     )
    #     result = await self.session.execute(query)
    #     diaries = result.scalars().all()
    #     return diaries or None
    # async def get_diary_list(
    #     self, user_id: int, params: Params = Depends()
    # ) -> Page[Diary]:
    #     query = (
    #         select(Diary)
    #         .where(Diary.user_id == user_id)
    #         .where(Diary.deleted_at.is_(None))  # 삭제되지 않은 일기만 검색
    #         .order_by(Diary.created_at.desc())
    #     )
    #
    #     return await paginate(self.session, query)  # type: ignore
    async def get_diary_list(
        self,
        user_id: int,
        params: Params = Depends(),
        word: Optional[str] = None,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Page[Diary]:
        query = (
            select(Diary)
            .where(Diary.user_id == user_id)
            .where(Diary.deleted_at.is_(None))
        )

        # 키워드 검색 (제목, 내용)
        if word:
            query = query.where(
                or_(Diary.title.ilike(f"%{word}%"), Diary.content.ilike(f"%{word}%"))
            )

        # 연도 검색
        if year:
            query = query.where(extract("year", Diary.write_date) == year)

        # 월 검색
        if month:
            query = query.where(extract("month", Diary.write_date) == month)

        # 정렬 조건 변경
        if year or month:
            # 연도나 월로 검색 시 write_date 기준 내림차순 정렬
            query = query.order_by(Diary.write_date.desc())
        else:
            # 기본적으로는 created_at 기준 내림차순 정렬
            query = query.order_by(Diary.created_at.desc())

        return await paginate(self.session, query)  # type: ignore

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

    async def restore_diary(self, diary_id: int, user_id: int) -> Diary | None:
        query = (
            select(Diary)
            .where(Diary.id == diary_id)
            .where(Diary.user_id == user_id)  # 사용자 검증 추가
            .where(Diary.deleted_at.is_not(None))  # 삭제된 일기만 복구 가능
        )
        result = await self.session.execute(query)
        diary = result.scalars().first()

        if diary:
            await diary.restore(self.session)
            return diary
        return None
