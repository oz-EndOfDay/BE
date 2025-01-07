from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from src.config.database.orm import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("friends.id"))
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    @classmethod
    def create(cls, user_id: int, friend_id: int, content: str) -> "Message":
        return cls(user_id=user_id, friend_id=friend_id, message=content)
