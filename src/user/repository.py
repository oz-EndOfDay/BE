# repository.py
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)  # 새로 생성된 객체를 갱신
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or user_id is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> User:
        user = await self.get_user_by_id(user_id)

        for key, value in user_data.items():
            if value is not None:  # None이 아닌 값만 업데이트
                setattr(user, key, value)

        await self.session.commit()
        return user

    async def soft_delete_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        user.deleted_at = datetime.utcnow()  # Soft delete 처리
        await self.session.commit()
