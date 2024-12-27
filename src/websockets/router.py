from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from src.websockets import database, models, schemas  # 절대 경로로 가져오기

router = APIRouter()


class WebSocketConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: int, message: str) -> None:
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_text(message)

    def get_connection(self, user_id: int) -> Optional[WebSocket]:  # Optional로 수정
        return self.active_connections.get(user_id)


manager = WebSocketConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: Session = Depends(database.get_db)) -> None:
    await manager.connect(websocket, user_id)

    try:
        while True:
            data = await websocket.receive_text()
            friend_id = 2  # 예시로 대화 상대의 ID를 지정 (실제로는 메시지에 포함시키거나 설정해야 함)

            # 메시지 저장
            db_websocket = models.Websockets(message=data, user_id=user_id, friend_id=friend_id)
            db.add(db_websocket)
            db.commit()
            db.refresh(db_websocket)

            # 대화 상대에게 메시지 전송
            if manager.get_connection(friend_id):
                message = f"Message from {user_id}: {data}"
                await manager.send_message(friend_id, message)

    except WebSocketDisconnect:
        manager.disconnect(user_id)
