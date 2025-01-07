from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from src.config.database.orm import Base
from src.diary.models import MoodEnum, WeatherEnum


class ExDiary(Base):
    __tablename__ = "ex_diaries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    friend_id = Column(Integer, ForeignKey("friends.id", ondelete="CASCADE"))

    title = Column(Text, nullable=False)
    write_date = Column(Date, nullable=False)
    weather: Mapped[WeatherEnum] = Column(Enum(WeatherEnum, create_type=False))
    mood: Mapped[MoodEnum] = Column(Enum(MoodEnum, create_type=False))
    content = Column(Text, nullable=False)
    img_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="ex_diaries")  # type: ignore
    friend = relationship("Friend", back_populates="ex_diaries", uselist=True)  # type: ignore

    @classmethod
    async def create(
        cls,
        user_id: int,
        friend_id: int,
        title: str,
        write_date: datetime,
        weather: WeatherEnum,
        mood: MoodEnum,
        content: str,
        img_url: Optional[str] = None,
    ) -> "ExDiary":
        return cls(
            user_id=user_id,
            friend_id=friend_id,
            title=title,
            write_date=write_date,
            weather=weather,
            mood=mood,
            content=content,
            img_url=img_url,
        )
