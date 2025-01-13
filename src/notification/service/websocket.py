from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError

from src.user.service.authentication import decode_access_token

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

    async def send_personal_message(
        self, message: str, user_id: int, noti_id: int
    ) -> None:
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(
                {"message": message, "noti_id": noti_id}
            )

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections.values():
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:

    # 헤더에서 토큰 검출. -> 프론트에서 웹소켓 연결 요청할 때 액세스 토큰 담을 수 있는 코드
    auth_header = websocket.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        await websocket.close(code=403)
        return

    token = auth_header.split(" ")[1]

    # 토큰 검증
    try:
        payload = decode_access_token(token)
        token_user_id = payload.get("user_id")

        if token_user_id is None or token_user_id != user_id:
            await websocket.close(code=403)
            return
    except JWTError:
        await websocket.close(code=403)
        return

    # 연결 관리
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"User {user_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await manager.broadcast(f"{user_id} 의 연결이 끊어졌습니다.")
