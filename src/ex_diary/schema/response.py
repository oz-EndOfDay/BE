from datetime import date, datetime

from pydantic import BaseModel

from src.user.models import User
from src.ex_diary.models import ExDiary


class ExDiaryBriefResponse(BaseModel):
    id: int
    author: str
    title: str
    write_date: date
    content: str
    created_at: datetime

    @classmethod
    def build(cls, ex_diary: ExDiary, user_id: int) -> "ExDiaryBriefResponse":
        author: str = ""
        if user_id == ex_diary.user_id:
            author = "Me"

        return cls(
            id=ex_diary.id or 0,
            author=author or "friend",
            title=ex_diary.title or "",
            write_date=ex_diary.write_date or date.today(),
            content=ex_diary.content or "",
            created_at=ex_diary.created_at or datetime.now(),
        )


class ExDiaryListResponse(BaseModel):
    diaries: list[ExDiaryBriefResponse]

    @classmethod
    def build(cls, ex_diaries: list[ExDiary], user_id: int) -> "ExDiaryListResponse":
        return cls(
            diaries=[
                ExDiaryBriefResponse.build(ex_diary=d, user_id=user_id)
                for d in ex_diaries
            ]
        )


class ExDiaryResponse(BaseModel):
    id: int
    title: str
    author: str
    write_date: date
    weather: str
    mood: str
    content: str
    img_url: str
    created_at: datetime

    @classmethod
    def build(cls, ex_diary: ExDiary, user: User) -> "ExDiaryResponse":
        return cls(
            id=ex_diary.id or 0,
            title=ex_diary.title or "",
            author=user.nickname or "",
            write_date=ex_diary.write_date or date.today(),
            weather=ex_diary.weather or "",
            mood=ex_diary.mood or "",
            content=ex_diary.content or "",
            img_url=ex_diary.img_url or "",
            created_at=ex_diary.created_at or datetime.now(),
        )
