from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Enum, String

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
    date = Column(DateTime, nullable=False)
    weather = Column(Enum(WeatherEnum))
    mood = Column(Enum(MoodEnum))
    content = Column(Text, nullable=False)
    img_url = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    deleted_at = Column(DateTime, nullable=True)


