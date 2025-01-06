from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.diary.models import Diary
from src.diary.service.tasks import delete_expired_diaries
from src.user.models import User


@pytest.mark.asyncio
async def test_delete_expired_diaries(async_session: AsyncSession):
    # 테스트용 만료된 일기 생성
    # Create a test user first
    test_user = User(
        name="Test User",
        email="test@example.com",
        nickname="testuser",
        password="password123",
    )
    async_session.add(test_user)
    await async_session.flush()  # Ensure user is saved to get an ID

    # Create an expired diary
    expired_diary = Diary(
        title="Expired Test Diary",
        user_id=test_user.id,
        write_date=datetime.now().date(),
        content="Test content",
        deleted_at=datetime.now() - timedelta(days=8),
    )
    async_session.add(expired_diary)
    await async_session.commit()

    # 태스크 실행
    await delete_expired_diaries(async_session)

    # 만료된 일기 삭제 확인
    result = await async_session.execute(
        select(Diary).where(Diary.id == expired_diary.id)
    )
    assert result.scalar_one_or_none() is None
