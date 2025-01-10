from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int) -> None:
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages (optional)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
