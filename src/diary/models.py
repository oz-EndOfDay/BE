from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.orm import Base


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
    __tablename__ = "diaries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(Text, nullable=False)
    write_date = Column(Date, nullable=False)
    weather: Column[Enum] = Column(Enum(WeatherEnum))
    mood: Column[Enum] = Column(Enum(MoodEnum))
    content = Column(Text, nullable=False)
    img_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    deleted_at = Column(DateTime, nullable=True)

    async def soft_delete(self, session: AsyncSession) -> None:
        self.deleted_at = datetime.now()  # type: ignore
        await session.commit()

    async def restore(self, session: AsyncSession) -> None:
        self.deleted_at = None  # type: ignore
        await session.commit()

    @classmethod
    async def create(
        cls,
        user_id: int,
        title: str,
        write_date: datetime,
        weather: WeatherEnum,
        mood: MoodEnum,
        content: str,
        img_url: str,
    ) -> "Diary":
        return cls(
            user_id=user_id,
            title=title,
            write_date=write_date,
            weather=weather,
            mood=mood,
            content=content,
            img_url=img_url,
        )
