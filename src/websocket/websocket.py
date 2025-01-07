from typing import Dict

from fastapi import Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection_async import get_db
from src.websocket.crud import create_message
from src.websocket.repository import ChatRepository
from src.websocket.schemas import MessageCreate


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int) -> None:
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


manager = ConnectionManager()


async def websocket_endpoint(
    websocket: WebSocket, user_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            friend_id_str, content = data.split(":", 1)
            friend_id = int(friend_id_str)

            message = MessageCreate(
                users_id=user_id, friend_id=friend_id, content=content
            )
            await create_message(db, message)

            await manager.send_personal_message(f"{user_id}: {content}", friend_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)