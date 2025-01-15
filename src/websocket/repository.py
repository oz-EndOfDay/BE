from typing import Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database.connection_async import get_db
from src.friend.models import Friend
from src.websocket.models import Message


class ChatRepository:
    def __init__(self, session: AsyncSession = Depends(get_db)):
        self.session = session

    async def save(self, message: Message) -> None:
        self.session.add(message)
        await self.session.commit()

    async def get_messages_by_room(self, chatroom_id: int) -> Sequence[Message]:
        # 1) DB에서 조회(I/O -> await)
        result = await self.session.execute(
            select(Message)
            .filter_by(chatroom_id=chatroom_id)
            .order_by(Message.created_at.asc())
        )

        # 2) 데이터를 ORM 객체로 변환(I/O 대기 없음)
        return result.scalars().all()

    async def get_latest_messages_by_room(
        self, user_id: int
    ) -> dict[int | None, Message | None]:
        # Fetch all accepted friends for the user
        result1 = await self.session.execute(
            select(Friend)
            .options(selectinload(Friend.user1), selectinload(Friend.user2))
            .filter(
                (
                    (Friend.user_id1 == user_id) | (Friend.user_id2 == user_id)
                )  # Friendships involving the user
                & (Friend.is_accept == True)  # Only accepted friendships
            )
        )
        friends = result1.scalars().all()

        # Prepare a mapping of friend IDs to their latest message
        latest_messages = {}
        for friend in friends:
            friend_id = friend.id
            result2 = await self.session.execute(
                select(Message)
                .filter_by(friend_id=friend_id)
                .order_by(Message.created_at.desc())  # Get the most recent message
                .limit(1)
            )
            latest_messages[friend_id] = result2.scalar_one_or_none()

        return latest_messages
