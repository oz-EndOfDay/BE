from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


class ExDiaryService:
    @staticmethod
    async def validate_friendship(
        user_id: int, friend_id: int, session: AsyncSession
    ) -> None:
        from src.friend.models import Friend

        friend_record = await session.execute(
            select(Friend).filter(
                or_(Friend.user_id1 == user_id, Friend.user_id2 == user_id),
                Friend.id == friend_id,
                Friend.is_accept == True,
            )
        )

        result = friend_record.scalar_one_or_none()

        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않거나 수락되지 않은 친구 관계입니다.",
            )
