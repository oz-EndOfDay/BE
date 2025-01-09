from typing import Sequence

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection_async import get_db
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
