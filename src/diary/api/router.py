import os
import shutil
from datetime import date

from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form

from src.diary.models import Diary, WeatherEnum, MoodEnum
from src.diary.reqository import DiaryReqository

router = APIRouter(prefix="/diary", tags=["Diary"])


@router.post(path="", status_code=status.HTTP_201_CREATED)
async def write_diary(
    title: str = Form(...),
    write_date: date = Form(...),
    weather: WeatherEnum = Form(...),
    mood: MoodEnum = Form(...),
    content: str = Form(...),
    image: UploadFile | str = File(default=None),
    diary_repo: DiaryReqository = Depends()
) -> tuple[int, dict[str, str]]:
    user_id = 1
    img_url = None

    if image and image.filename:  # 추가 조건 체크
        image_filename: str = f"{user_id}_{image.filename}"
        img_url = os.path.join("src/diary/img", image_filename)

        with open(img_url, "wb") as f:
            shutil.copyfileobj(image.file, f)

    new_diary = await Diary.create(
        user_id=user_id,
        title=title,
        write_date=write_date,
        weather=weather,
        mood=mood,
        content=content,
        img_url=img_url
    )

    try:
        await diary_repo.save(new_diary)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail=str(e))

    return 201, {
        "message": "일기 작성을 성공적으로 마쳤습니다", "status": "success"
    }
