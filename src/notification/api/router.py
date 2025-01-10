from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.config.database.connection import get_async_session
from src.notification.models import Notification
from src.notification.repository import NotificationRepository
from src.notification.service.websocket import manager

router = APIRouter(prefix="/notifications", tags=["Notifications"])
settings = Settings()


@router.post("")
async def create_notification(
    user_id: int,
    title: str,
    message: str,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str | Notification]:
    notification = Notification(user_id=user_id, title=title, message=message)
    noti_repo = NotificationRepository(session)
    await noti_repo.create_notification(notification)
    return {"status": "success", "data": notification}


@router.post("/send")
async def send_notification(user_id: int, message: str) -> dict[str, str]:
    await manager.broadcast(f"Notification for user {user_id}: {message}")
    return {"status": "sent"}


@router.put("/{notification_id}")
async def mark_as_read(
    notification_id: int, session: AsyncSession = Depends(get_async_session)
) -> dict[str, str]:
    noti_repo = NotificationRepository(session=session)
    result = await noti_repo.mark_as_read(notification_id)
    if result:
        return {"status": "success"}
    else:
        return {"status": "failed"}
