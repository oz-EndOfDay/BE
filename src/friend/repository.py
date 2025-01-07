from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.friend.models import Friend
from src.friend.schema.response import FriendList, FriendResponse


class FriendRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_friend_request(self, user_id1: int, user_id2: int) -> Friend:
        friend_request = Friend(user_id1=user_id1, user_id2=user_id2)
        self.session.add(friend_request)
        await self.session.commit()
        await self.session.refresh(friend_request)
        return friend_request

    async def accept_friend_request(self, friend_request_id: int) -> Friend:
        # 친구 요청 조회
        result = await self.session.execute(
            select(Friend).filter(Friend.id == friend_request_id)
        )
        friend_request = result.scalar_one_or_none()

        if not friend_request:
            raise ValueError("Friend request not found")

        # 친구 요청 수락 처리
        friend_request.is_accept = True
        await self.session.commit()
        await self.session.refresh(friend_request)

        return friend_request
