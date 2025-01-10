from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.notification.models import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession = Depends(get_async_session)):
        self.session = session

    async def create_notification(self, notification: Notification) -> None:
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)

    async def mark_as_read(self, notification_id: int) -> bool:
        result = await self.session.execute(
            select(Notification).filter_by(notification_id=notification_id)
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            await self.session.commit()
            return True
        else:
            return False
