from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: int) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, user_id: int) -> None:
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections.values():
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    # 사용자 연결 처리
    await manager.connect(websocket, user_id)
    try:
        while True:
            # 메시지 수신 및 처리
            data = await websocket.receive_text()
            if data == "ping":
                # 클라이언트 응답
                await manager.send_personal_message("pong", user_id)
            else:
                # 메시지 브로드캐스트
                await manager.broadcast(f"User {user_id} says: {data}")
    except WebSocketDisconnect:
        # 연결 해제 처리
        manager.disconnect(user_id)
        await manager.broadcast(f"User {user_id} left the chat")
    except Exception as e:
        print(f"Error: {e}")
        manager.disconnect(user_id)
