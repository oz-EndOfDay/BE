from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.websocket.models import Message
from src.websocket.schemas import MessageCreate


async def create_message(db: AsyncSession, message: MessageCreate) -> Message:
    db_message = Message.create(
        user_id=message.user_id, friend_id=message.friend_id, content=message.content
    )
    db.add(db_message)
    await db.commit()
    await db.refresh(db_message)
    return db_message


async def get_messages(db: AsyncSession, user_id: int, friend_id: int) -> list[Message]:
    result = await db.execute(
        select(Message)
        .filter(
            (Message.user_id == user_id) & (Message.friend_id == friend_id)
            | (Message.user_id == friend_id) & (Message.friend_id == user_id)
        )
        .order_by(Message.created_at.asc())
    )
    return list(result.scalars().all())
