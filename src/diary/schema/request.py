from datetime import date
from typing import Optional

from pydantic import BaseModel

from src.diary.models import WeatherEnum, MoodEnum


class WriteDiaryRequest(BaseModel):
    title: str
    write_date: date
    weather: WeatherEnum
    mood: MoodEnum
    content: str
    image: Optional[str] = None  # 이미지 URL이나 파일명으로 변경