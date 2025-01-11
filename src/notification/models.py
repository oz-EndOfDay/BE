from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from src.config.database.orm import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 알림 수신자
    title = Column(String, nullable=False)  # 알림 제목
    message = Column(String, nullable=True)  # 알림 내용
    is_read = Column(Boolean, default=False)  # 읽음 상태
    read_at = Column(DateTime, default=datetime.now())  # 읽은 시간
    created_at = Column(DateTime, default=datetime.now())  # 알림 보낸 시간

    user = relationship("User", back_populates="notifications")  # type: ignore
