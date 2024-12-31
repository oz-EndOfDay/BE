from typing import Dict

from app.auth import get_current_user
from app.database import get_db
from app.models import Message
from app.schemas import MessageCreate
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: str) -> None:
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: str) -> None:
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, user_id: str, db: Session = Depends(get_db)
) -> None:
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            recipient_id, content = data.split(":", 1)
            await manager.send_personal_message(f"{user_id}: {content}", recipient_id)

            # 메시지 저장
            new_message = Message.create(
                user_id=int(user_id), friend_id=int(recipient_id), content=content
            )
            db.add(new_message)
            db.commit()
    except WebSocketDisconnect:
        manager.disconnect(user_id)


@router.post("/send_message/")
async def send_message(
    message: MessageCreate,
    current_user: int = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    new_message = Message.create(
        user_id=current_user, friend_id=message.recipient_id, content=message.content
    )
    db.add(new_message)
    db.commit()

    await manager.send_personal_message(
        f"{current_user}: {message.content}", str(message.recipient_id)
    )
    return {"status": "success", "message": "Message sent"}
