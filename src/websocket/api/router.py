import json
from typing import Dict, Tuple
from urllib.parse import parse_qs

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection_async import get_db
from src.user.service.authentication import decode_access_token
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
        self, message_data: Dict[str, str], sender_id: int, friend_id: int
    ) -> None:
        for (user_id, room_id), websocket in self.active_connections.items():
            if room_id == friend_id and user_id != sender_id:
                await websocket.send_json(message_data)


manager = ConnectionManager()


@router.websocket("/ws/{friend_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    friend_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    try:
        # URL 쿼리 파라미터에서 토큰 추출
        query_params = parse_qs(websocket.scope["query_string"].decode())
        token = query_params.get("token", [None])[0]
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # 토큰 검증 및 사용자 ID 추출
        try:
            payload = decode_access_token(token)
            user_id = payload["user_id"]
        except Exception as e:
            print(f"Token decoding error: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # WebSocket 연결 등록
        await manager.connect(websocket, user_id, friend_id)

        # 이전 채팅 기록 조회 및 전송
        messages_query = (
            select(Message)
            .where(Message.friend_id == friend_id)
            .order_by(Message.created_at)
        )
        messages_result = await db.execute(messages_query)
        previous_messages = messages_result.scalars().all()

        for msg in previous_messages:
            if msg.user_id == user_id:
                await websocket.send_json({"sender": "Me", "message": msg.message})
            else:
                await websocket.send_json({"sender": "Friend", "message": msg.message})

        # 실시간 메시지 수신 및 처리 루프
        while True:
            raw_content = await websocket.receive_text()

            # JSON 문자열을 딕셔너리로 변환
            try:
                content_data = json.loads(raw_content)  # {"message": "안녕하세요"}
                content = content_data.get("message", "")  # 실제 메시지 내용 추출
            except json.JSONDecodeError:
                # 만약 JSON 형식이 아니라면 기본적으로 raw_content를 사용
                content = raw_content

            # 새 메시지 데이터베이스에 저장
            new_message = Message(
                user_id=user_id,
                friend_id=friend_id,
                message=content,
            )
            db.add(new_message)
            await db.commit()

            # 발신자에게 메시지 표시
            sender_message = {"sender": "Me", "message": content}
            await websocket.send_json(sender_message)

            # 수신자에게 메시지 전송
            recipient_message = {"sender": "Friend", "message": content}
            await manager.send_personal_message(recipient_message, user_id, friend_id)

    except WebSocketDisconnect:
        manager.disconnect(user_id, friend_id)

    except Exception as e:
        print(f"Unexpected error: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)


@router.post("/send_message/")
async def send_message(
    message: MessageCreate,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    # 데이터베이스에 새 메시지 저장
    new_message = Message(
        user_id=message.user_id,
        friend_id=message.friend_id,
        message=message.content,
    )
    db.add(new_message)
    await db.commit()

    # 발신자에게 보낼 메시지
    sender_message = {
        "sender": "Me",
        "message": message.content,
    }

    # 수신자에게 보낼 메시지
    recipient_message = {
        "sender": f"User {message.user_id}",
        "message": message.content,
    }

    # 발신자에게 메시지 전송 (현재 연결된 WebSocket 클라이언트)
    await manager.send_personal_message(
        sender_message, message.user_id, message.friend_id
    )

    # 수신자에게 메시지 전송 (현재 연결된 WebSocket 클라이언트)
    await manager.send_personal_message(
        recipient_message, message.user_id, message.friend_id
    )

    return {"status": "success", "message": "Message sent"}


# from typing import Dict, Tuple
#
# from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src.config.database.connection_async import get_db
# from src.friend.models import Friend
# from src.user.models import User
# from src.user.service.authentication import decode_access_token
# from src.websocket.models import Message
# from src.websocket.schemas import MessageCreate
#
# router = APIRouter()
#
#
# # WebSocket 연결과 메시지 관리를 위한 클래스
# class ConnectionManager:
#     def __init__(self) -> None:
#         self.active_connections: Dict[Tuple[int, int], WebSocket] = {}
#
#     async def connect(self, websocket: WebSocket, user_id: int, friend_id: int) -> None:
#         # 새로운 WebSocket 연결을 수락하고 저장
#         await websocket.accept()
#         self.active_connections[(user_id, friend_id)] = websocket
#
#     def disconnect(self, user_id: int, friend_id: int) -> None:
#         # WebSocket 연결 종료 시 연결 제거
#         if (user_id, friend_id) in self.active_connections:
#             del self.active_connections[(user_id, friend_id)]
#
#     async def send_personal_message(
#         self, message: str, sender_id: int, friend_id: int
#     ) -> None:
#         for (user_id, room_id), websocket in self.active_connections.items():
#             if room_id == friend_id and user_id != sender_id:
#                 await websocket.send_text(message)
#
#
# manager = ConnectionManager()
#
#
# @router.websocket("/ws/{friend_id}")
# async def websocket_endpoint(
#     websocket: WebSocket,
#     friend_id: int,
#     db: AsyncSession = Depends(get_db),
# ) -> None:
#     try:
#         # 헤더에서 토큰 추출 및 검증
#         authorization = websocket.headers.get("Authorization")
#         if not authorization:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             return
#
#         # Bearer 토큰에서 실제 토큰 추출
#         try:
#             token = authorization.split(" ")[1]
#             payload = decode_access_token(token)
#             user_id = payload["user_id"]
#
#         except Exception:
#             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#             return
#
#         await manager.connect(websocket, user_id, friend_id)
#
#         # 이전 채팅 기록 조회
#         messages_query = (
#             select(Message)
#             .where(Message.friend_id == friend_id)
#             .order_by(Message.created_at)
#         )
#         messages_result = await db.execute(messages_query)
#         previous_messages = messages_result.scalars().all()
#
#         # 친구 정보 조회
#         friend_query = select(Friend).where(Friend.id == friend_id)
#         friend_result = await db.execute(friend_query)
#         friend_record = friend_result.scalar_one_or_none()
#
#         # 친구의 닉네임 조회
#         friend_name = ""
#         if friend_record:
#             if friend_record.user_id1 != user_id:
#                 user_query = select(User).where(User.id == friend_record.user_id1)
#                 user_result = await db.execute(user_query)
#                 user = user_result.scalar_one_or_none()
#                 if user:
#                     friend_name = user.nickname
#             else:
#                 user_query = select(User).where(User.id == friend_record.user_id2)
#                 user_result = await db.execute(user_query)
#                 user = user_result.scalar_one_or_none()
#                 if user:
#                     friend_name = user.nickname
#
#         # 이전 메시지들을 클라이언트에게 전송
#         for msg in previous_messages:
#             if msg.user_id == user_id:
#                 await websocket.send_text(f"Me : {msg.message}")
#             else:
#                 await websocket.send_text(f"{friend_name} : {msg.message}")
#
#         # 친구의 닉네임 조회
#         friend_name = ""
#         if friend_record:
#             if friend_record.user_id1 == user_id:
#                 user_query = select(User).where(User.id == friend_record.user_id1)
#                 user_result = await db.execute(user_query)
#                 user = user_result.scalar_one_or_none()
#                 if user:
#                     friend_name = user.nickname
#             else:
#                 user_query = select(User).where(User.id == friend_record.user_id2)
#                 user_result = await db.execute(user_query)
#                 user = user_result.scalar_one_or_none()
#                 if user:
#                     friend_name = user.nickname
#
#         # 실시간 메시지 수신 및 처리
#         while True:
#             content = await websocket.receive_text()
#             async with db as session:
#                 new_message = Message(
#                     user_id=user_id, friend_id=friend_id, message=content
#                 )
#                 session.add(new_message)
#                 await session.commit()
#
#             # 발신자에게 메시지 표시
#             await websocket.send_text(f"Me : {content}")
#
#             # 수신자에게 메시지 전송
#             await manager.send_personal_message(
#                 f"{friend_name} : {content}", user_id, friend_id
#             )
#     except WebSocketDisconnect:
#         manager.disconnect(user_id, friend_id)
#
#
# @router.post("/send_message/")
# async def send_message(
#     message: MessageCreate,
#     db: AsyncSession = Depends(get_db),
# ) -> dict[str, str]:
#     new_message = Message(
#         user_id=message.user_id, friend_id=message.friend_id, message=message.content
#     )
#     db.add(new_message)
#     await db.commit()
#
#     await manager.send_personal_message(
#         f"User {message.user_id}: {message.content}", message.user_id, message.friend_id
#     )
#     return {"status": "success", "message": "Message sent"}
