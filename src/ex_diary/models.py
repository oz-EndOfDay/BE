from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, relationship

from src.config.database.orm import Base


class WeatherEnum(str, PyEnum):
    clear = "맑음"
    some_clouds = "구름 조금"
    cloudy = "흐림"
    rainy = "비"
    snowy = "눈"


class MoodEnum(str, PyEnum):
    happy = "기쁨"
    good = "좋음"
    normal = "보통"
    tired = "지침"
    sad = "슬픔"


class ExDiary(Base):
    __tablename__ = "ex_diaries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', nullable=False))
    friend_id = Column(Integer, ForeignKey('friends.id', ondelete='CASCADE'), nullable=False)

    title = Column(Text, nullable=False)
    write_date = Column(Date, nullable=False)
    weather: Mapped[WeatherEnum] = Column(Enum(WeatherEnum))
    mood: Mapped[MoodEnum] = Column(Enum(MoodEnum))
    content = Column(Text, nullable=False)
    img_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships
    user = relationship("User", back_populates="ex_diaries")
    friend = relationship("Friend", back_populates="ex_diaries")

    @classmethod
    async def create(
        cls,
        title: str,
        write_date: datetime,
        weather: WeatherEnum,
        mood: MoodEnum,
        content: str,
        img_url: str,
    ) -> "ExDiary":
        return cls(
            title=title,
            write_date=write_date,
            weather=weather,
            mood=mood,
            content=content,
            img_url=img_url,
        )