from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta

from src.user.models import User


async def cleanup_deleted_users(session: AsyncSession):
    threshold_date = datetime.now() - timedelta(days=7)

    # 오래된 소프트 삭제된 사용자 찾기
    users_to_delete = await session.execute(
        select(User).where(User.deleted_at < threshold_date)
    )

    # 결과에서 사용자 객체 가져오기
    users_to_delete = users_to_delete.scalars().all()

    # 각 사용자 객체 삭제
    for user in users_to_delete:
        await session.delete(user)

    await session.commit()