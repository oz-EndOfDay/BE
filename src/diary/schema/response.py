from datetime import date

from pydantic import BaseModel, ConfigDict

from src.diary.models import Diary


class DiaryBriefResponse(BaseModel):
    id: int
    title: str
    write_date: date
    content: str

    @classmethod
    def build(cls, diary: Diary):
        return cls(
            id = diary.id,
            title = diary.title,
            write_date = diary.write_date,
            content = diary.content
        )

class DiaryListResponse(BaseModel):
    diaries: list[DiaryBriefResponse]

    @classmethod
    def build(cls, diaries: list[Diary]):
        return cls(
            diaries=[DiaryBriefResponse.build(diary=d) for d in diaries]
        )