from typing import Dict, Tuple

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.config.database.connection_async import get_db
from src.websocket.api.auth import get_current_user
from src.websocket.models import Message
from src.websocket.schemas import MessageCreate

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[Tuple[int, int], WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int, friend_id: int) -> None:
        await websocket.accept()
        self.active_connections[(user_id, friend_id)] = websocket

    def disconnect(self, user_id: int, friend_id: int) -> None:
        if (user_id, friend_id) in self.active_connections:
            del self.active_connections[(user_id, friend_id)]

    async def send_personal_message(
        self, message: str, user_id: int, friend_id: int
    ) -> None:
        if (friend_id, user_id) in self.active_connections:
            await self.active_connections[(friend_id, user_id)].send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}/{friend_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: int, friend_id: int, db: Session = Depends(get_db)
) -> None:
    await manager.connect(websocket, user_id, friend_id)
    try:
        while True:
            content = await websocket.receive_text()
            new_message = Message.create(
                user_id=user_id, friend_id=friend_id, content=content
            )
            db.add(new_message)
            db.commit()

            await manager.send_personal_message(
                f"{user_id}: {content}", user_id, friend_id
            )
    except WebSocketDisconnect:
        manager.disconnect(user_id, friend_id)


@router.post("/send_message/")
async def send_message(
    message: MessageCreate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    new_message = Message.create(
        user_id=current_user, friend_id=message.friend_id, content=message.content
    )
    db.add(new_message)
    db.commit()

    await manager.send_personal_message(
        f"{current_user}: {message.content}", current_user, message.friend_id
    )
    return {"status": "success", "message": "Message sent"}
