import uuid
from datetime import date, datetime
from typing import Optional, Union

import boto3
from botocore.exceptions import ClientError
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    UploadFile,
    status,
)

from src.config import Settings
from src.diary.models import MoodEnum, WeatherEnum
from src.ex_diary.models import ExDiary
from src.ex_diary.repository import ExDiaryRepository
from src.user.service.authentication import authenticate

router = APIRouter(prefix="/ex_diary", tags=["Exchange Diary"])
settings = Settings()


@router.post(
    path="/{friend_id}",
    summary="교환일기 작성",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
)
async def write_diary(
    user_id: int = Depends(authenticate),
    friend_id: int = Path(..., description="친구 관계 ID(친구의 유저 ID(X)"),
    title: str = Form(...),
    write_date: date = Form(...),
    weather: WeatherEnum = Form(...),
    mood: MoodEnum = Form(...),
    content: str = Form(...),
    image: Union[UploadFile, str] = File(default=None),
    ex_diary_repo: ExDiaryRepository = Depends(),
) -> tuple[int, dict[str, str]]:
    # S3 클라이언트 설정
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    img_url: Optional[str] = None

    # 이미지 업로드 처리
    if isinstance(image, UploadFile) and image.filename:
        try:
            # 고유한 파일명 생성
            image_filename = (
                f"ex_diary_{user_id}_{uuid.uuid4()}{Path(image.filename).suffix}"
            )

            # S3에 업로드
            s3_key = f"ex_diaries/{image_filename}"
            s3_client.upload_fileobj(
                image.file,
                settings.S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={"ContentType": image.content_type},
            )

            # 공개 URL 생성
            img_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

        except ClientError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"S3 업로드 오류: {str(e)}",
            )

    # 날짜를 datetime으로 변환
    write_date_datetime = datetime.combine(write_date, datetime.min.time())

    # 새 다이어리 생성
    new_ex_diary = await ExDiary.create(
        user_id=user_id,
        friend_id=friend_id,
        title=title,
        write_date=write_date_datetime,  # datetime으로 변경
        weather=weather,
        mood=mood,
        content=content,
        img_url=img_url or "",
    )

    try:
        await ex_diary_repo.save(new_ex_diary)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return 201, {
        "message": "일기가 성공적으로 생성되었습니다.",
        "status": "success",
    }
