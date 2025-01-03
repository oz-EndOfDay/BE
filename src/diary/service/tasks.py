from datetime import datetime, timedelta

from celery import shared_task
from celery.schedules import crontab
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.connection import AsyncSessionFactory
from diary.models import Diary


async def delete_expired_diaries_task() -> None:
    async with AsyncSessionFactory() as session:
        async with session.begin():
            await delete_expired_diaries(session)


@shared_task(name="tasks.delete_expired_diaries")  # type: ignore
async def delete_expired_diaries(session: AsyncSession) -> None:
    seven_days_ago = datetime.now() - timedelta(days=7)

    # 대량 삭제로 변경
    await session.execute(
        delete(Diary).where(
            Diary.deleted_at.isnot(None), Diary.deleted_at <= seven_days_ago
        )
    )
    await session.commit()


# Celery beat 설정 (celery_config.py)
CELERYBEAT_SCHEDULE = {
    "delete-expired-diaries": {
        "task": "tasks.delete_expired_diaries",
        "schedule": crontab(hour="0", minute="0"),  # 매일 자정에 실행
    },
}
