from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Enum, String, Date

from src.config.database.orm import Base
from src.user.models import User


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

class Diary(Base):
    __tablename__ = "diary"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(Text, nullable=False)
    write_date = Column(Date, nullable=False)
    weather = Column(Enum(WeatherEnum))
    mood = Column(Enum(MoodEnum))
    content = Column(Text, nullable=False)
    img_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    @classmethod
    async def create(cls, user_id: int, title: str, write_date: datetime, weather: WeatherEnum, mood: MoodEnum, content: str, img_url: str):
        return cls(user_id=user_id, title=title, write_date=write_date, weather=weather, mood=mood, content=content, img_url=img_url)