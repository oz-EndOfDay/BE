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
    logging.info("클린업 코드 실행")
    # 오래된 소프트 삭제된 사용자 찾기
    result = await session.execute(select(User).where(User.deleted_at < threshold_date))
    logging.info(result)
    # 결과에서 사용자 객체 가져오기
    users_to_delete = result.scalars().all()

    # 각 사용자 객체 삭제
    for user in users_to_delete:
        await session.delete(user)

    await session.commit()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def periodic_cleanup() -> None:
    while True:
        logger.info("주기적 클린업 시작")
        session_gen = get_async_session()
        try:
            session = await anext(session_gen)
            await cleanup_deleted_users(session)
            logger.info("주기적 클린업 실행 완료")
        finally:
            try:
                await session_gen.aclose()
            except StopAsyncIteration:
                pass
        logger.info("15초 대기 시작")
        await asyncio.sleep(3600)  # 1시간마다 7일 지난 유저 삭제
