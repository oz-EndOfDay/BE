from datetime import date
from typing import Optional

from pydantic import BaseModel

from diary.models import MoodEnum, WeatherEnum


# 이미지가 항시 존재하지 않는데 계속 요구해서 사용하지 않음
class WriteDiaryRequest(BaseModel):
    title: str
    write_date: date
    weather: WeatherEnum
    mood: MoodEnum
    content: str
    image: Optional[str] = None  # 이미지 URL이나 파일명으로 변경
