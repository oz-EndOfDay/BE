from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.friend.models import Friend


class FriendRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # 친구 신청 repo
    async def create_friend_request(self, user_id1: int, user_id2: int) -> Friend:
        friend_request = Friend(
            user_id1=user_id1, user_id2=user_id2
        )  # 현재 유저 id 가 user_id1
        self.session.add(friend_request)
        await self.session.commit()
        await self.session.refresh(friend_request)
        return friend_request

    # 친구 요청 목록 조회 repo
    async def get_friend_request_list(self, user_id: int) -> list[Friend]:
        result = await self.session.execute(
            select(Friend).filter(
                Friend.user_id2
                == user_id,  # 요청자 아이디가 user_id1 에 들어가므로 요청 받은 리스트는 2번이 현재 유저 아이디
                Friend.is_accept == False,  # 수락되지 않은 요청만 조회
            )
        )
        return list(result.scalars().all())

    # 친구 수락 repo
    async def accept_friend_request(self, user_id: int, friend_request_id: int) -> bool:

        result = await self.session.execute(
            select(Friend).filter(Friend.id == friend_request_id)
        )

        friend_request = result.scalar_one_or_none()

        if not friend_request:
            raise ValueError("요청한 사용자를 찾을 수 없습니다.")

        if friend_request.user_id2 == user_id:
            friend_request.is_accept = True

        await self.session.commit()
        await self.session.refresh(friend_request)

        return True

    # 친구 목록 조회 repo
    async def get_friends(self, user_id: int) -> list[Friend]:
        result = await self.session.execute(
            select(Friend).filter(
                (Friend.user_id1 == user_id) & (Friend.is_accept == True)
                | (Friend.user_id2 == user_id) & (Friend.is_accept == True)
            )
        )
        return list(result.scalars().all())

    async def check_friendship(self, user_id: int, friend_id: int) -> Optional[Friend]:
        result = await self.session.execute(
            select(Friend).filter(
                ((Friend.user_id1 == user_id) & (Friend.user_id2 == friend_id))
                | ((Friend.user_id1 == friend_id) & (Friend.user_id2 == user_id))
            )
        )
        return result.scalar_one_or_none()

    # 친구 삭제 repo
    async def delete_friend(self, user_id: int, friend_id: int) -> bool:
        result = await self.session.execute(
            select(Friend).filter(
                (Friend.id == friend_id)
                & ((Friend.user_id1 == user_id) | (Friend.user_id2 == user_id))
            )
        )
        friend = result.scalar_one_or_none()

        if not friend:
            return False

        await self.session.execute(delete(Friend).where(Friend.id == friend_id))
        await self.session.commit()
        return True
