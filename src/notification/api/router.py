from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.config.database.connection import get_async_session
from src.notification.models import Notification
from src.notification.repository import NotificationRepository
from src.notification.schema.request import NotificationCreate
from src.notification.schema.response import (
    NotificationInDBResponse,
    NotificationResponse,
)
from src.notification.service.websocket import manager

router = APIRouter(prefix="/notifications", tags=["Notifications"])
settings = Settings()


@router.post("", summary="알림 생성하기", response_model=NotificationResponse)
async def create_notification(
    notification: NotificationCreate,
    session: AsyncSession = Depends(get_async_session),
) -> NotificationResponse:
    db_notification = Notification(**notification.model_dump())
    noti_repo = NotificationRepository(session)
    created_notification = await noti_repo.create_notification(db_notification)
    notification_in_db = NotificationInDBResponse.model_validate(created_notification)
    return NotificationResponse(status="success", data=notification_in_db)


@router.post("/send", summary="알림 유저에게 전송 하기", response_model=None)
async def send_notification(user_id: int, message: str) -> Dict[str, str]:
    try:
        print("알림 전송")
        await manager.broadcast(f"Notification for user {user_id}: {message}")
        return {"status": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}", summary="알림 확인 시 '읽음' 상태 변경", response_model=None)
async def mark_as_read(
    notification_id: int, session: AsyncSession = Depends(get_async_session)
) -> dict[str, str]:
    noti_repo = NotificationRepository(session=session)
    result = await noti_repo.mark_as_read(notification_id)
    if result:
        return {"status": "success"}
    else:
        return {"status": "failed"}
