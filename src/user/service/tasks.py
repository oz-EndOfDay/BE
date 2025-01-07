import asyncio
import logging
from datetime import datetime, timedelta

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.config.database.connection import get_async_session
from src.user.models import User


async def cleanup_deleted_users(session: AsyncSession) -> None:
    threshold_date = datetime.now() - timedelta(days=7)
    # 오래된 소프트 삭제된 사용자 찾기
    result = await session.execute(select(User).where(User.deleted_at < threshold_date))
    # 결과에서 사용자 객체 가져오기
    users_to_delete = result.scalars().all()

    # 각 사용자 객체 삭제
    for user in users_to_delete:
        await session.delete(user)
    await session.commit()


async def periodic_cleanup() -> None:
    while True:
        session_gen = get_async_session()
        try:
            session = await anext(session_gen)
            await cleanup_deleted_users(session)
        finally:
            try:
                await session_gen.aclose()
            except StopAsyncIteration:
                pass
        await asyncio.sleep(3600)  # 1시간마다 7일 지난 유저 삭제
