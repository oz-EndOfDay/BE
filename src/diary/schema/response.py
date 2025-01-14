from datetime import date
from typing import Dict

from pydantic import BaseModel

from src.diary.models import Diary, MoodEnum


class DiaryBriefResponse(BaseModel):
    id: int
    title: str
    write_date: date
    content: str

    @classmethod
    def build(cls, diary: Diary) -> "DiaryBriefResponse":
        return cls(
            id=diary.id or 0,
            title=diary.title or "",
            write_date=diary.write_date or date.today(),
            content=diary.content or "",
        )


class DiaryListResponse(BaseModel):
    diaries: list[DiaryBriefResponse]

    @classmethod
    def build(cls, diaries: list[Diary]) -> "DiaryListResponse":
        return cls(diaries=[DiaryBriefResponse.build(diary=d) for d in diaries])


class DiaryDetailResponse(BaseModel):
    id: int
    title: str
    write_date: date
    weather: str
    mood: str
    content: str
    img_url: str

    class Config:
        from_attributes = True


class DiaryAnalysisResponse(BaseModel):
    diary_id: int
    # diary_content: str    # 반환 시 일기 내용은 반ㅏ하ㄱ지 않음
    diary_analysis_result: str
    advice_analysis_result: str


class MoodStatisticsResponse(BaseModel):
    happy: int
    good: int
    normal: int
    tired: int
    sad: int

    @classmethod
    def build(cls, mood_stats: Dict[MoodEnum, int]) -> "MoodStatisticsResponse":
        return cls(
            happy=mood_stats[MoodEnum.happy],
            good=mood_stats[MoodEnum.good],
            normal=mood_stats[MoodEnum.normal],
            tired=mood_stats[MoodEnum.tired],
            sad=mood_stats[MoodEnum.sad],
        )
