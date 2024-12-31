from datetime import date

from pydantic import BaseModel, ConfigDict

from diary.models import Diary


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
