import logging
import os
import uuid
from datetime import date, datetime
from typing import Optional, Union

import boto3
import openai
from botocore.exceptions import ClientError
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Path,
    Query,
    UploadFile,
    status,
)
from fastapi_pagination import Page, Params

from src.config import Settings
from src.diary.models import Diary, MoodEnum, WeatherEnum
from src.diary.repository import DiaryRepository
from src.diary.schema.response import (
    DiaryAnalysisResponse,
    DiaryBriefResponse,
    DiaryDetailResponse,
    DiaryListResponse,
)
from src.diary.service.AIAnalysis import AIAnalysisService
from src.user.service.authentication import authenticate

router = APIRouter(prefix="/diary", tags=["Diary"])
settings = Settings()

logger = logging.getLogger(__name__)

@router.post(
    path="",
    summary="일기 작성",
    response_model=None,
    status_code=status.HTTP_201_CREATED,
)
async def write_diary(
    user_id: int = Depends(authenticate),
    title: str = Form(...),
    write_date: date = Form(...),
    weather: WeatherEnum = Form(...),
    mood: MoodEnum = Form(...),
    content: str = Form(...),
    image: Union[UploadFile, str] = File(default=None),
    diary_repo: DiaryRepository = Depends(),
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
    if image and image.filename:  # type: ignore
        try:
            # 파일 포인터 초기화
            image.file.seek(0)  # type: ignore

            # 파일 크기 확인
            file_size = len(image.file.read())  # type: ignore
            # 다시 포인터 초기화
            image.file.seek(0)  # type: ignore

            # print(f"File details:")
            # print(f"Filename: {image.filename}")
            # print(f"File size: {file_size} bytes")
            # print(f"Content type: {image.content_type}")

            if file_size == 0:
                print("Warning: Empty file received")
                return 201, {
                    "message": "이미지 파일이 비어있습니다.",
                    "status": "warning",
                }

            # 고유한 파일명 생성
            image_filename = f"diary_{user_id}_{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"  # type: ignore

            # S3에 업로드
            s3_key = f"diaries/{image_filename}"
            s3_client.upload_fileobj(
                image.file,  # type: ignore
                settings.S3_BUCKET_NAME,
                s3_key,
                ExtraArgs={"ContentType": image.content_type},  # type: ignore
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
    new_diary = await Diary.create(
        user_id=user_id,
        title=title,
        write_date=write_date_datetime,  # datetime으로 변경
        weather=weather,
        mood=mood,
        content=content,
        img_url=img_url or "",
    )

    try:
        await diary_repo.save(new_diary)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return 201, {
        "message": "일기가 성공적으로 생성되었습니다.",
        "status": "success",
    }


@router.get(
    path="",
    summary="전체 일기 검색 및 조회",
    status_code=status.HTTP_200_OK,
    response_model=Page[DiaryBriefResponse],
)
async def diary_list(
    user_id: int = Depends(authenticate),
    params: Params = Depends(),
    word: Optional[str] = Query(None, description="검색 키워드"),
    year: Optional[int] = Query(None, description="검색 연도"),
    month: Optional[int] = Query(None, description="검색 월"),
    diary_repo: DiaryRepository = Depends(),
) -> Page[DiaryBriefResponse]:
    diaries = await diary_repo.get_diary_list(
        user_id, params, word=word, year=year, month=month
    )

    if not diaries.items:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message": "검색 결과가 없습니다.",
                "status": "success",
            },
        )

    return diaries  # type: ignore
    # return DiaryListResponse.build(diaries=list(diaries))


@router.get(
    path="/deleted",
    summary="삭제된 일기(7일 이내) 확인",
    status_code=status.HTTP_200_OK,
    response_model=DiaryListResponse,
)
async def diary_list_deleted(
    user_id: int = Depends(authenticate),
    diary_repo: DiaryRepository = Depends(),
) -> DiaryListResponse:

    diaries = await diary_repo.get_deleted_diary_list(user_id)

    if not diaries:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message": "You haven't deleted any diary entries yet.",
                "status": "success",
            },
        )

    return DiaryListResponse.build(diaries=list(diaries))


@router.get(
    path="/{diary_id}",
    summary="선택한 일기(1개) 조회",
    status_code=status.HTTP_200_OK,
    response_model=DiaryDetailResponse,
)
async def diary_detail(
    diary_id: int = Path(..., description="조회할 일기의 고유 식별자"),
    user_id: int = Depends(authenticate),
    diary_repo: DiaryRepository = Depends(),
) -> Diary:

    if not (diary := await diary_repo.get_diary_detail(diary_id=diary_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested diary entry could not be found.",
        )

    if diary.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own diary entries.",
        )

    return DiaryDetailResponse.model_validate(diary)  # type: ignore


@router.delete(
    path="/{diary_id}",
    summary="선택한 일기 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_diary(
    diary_id: int,
    user_id: int = Depends(authenticate),
    diary_repo: DiaryRepository = Depends(),
) -> tuple[int, dict[str, str]]:

    if not (diary := await diary_repo.get_diary_detail(diary_id=diary_id)):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The requested diary entry could not be found.",
        )

    if diary.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own diary entries.",
        )

    await diary_repo.delete(diary)
    return 204, {"message": "Diary entry successfully deleted.", "status": "success"}


@router.patch("/{diary_id}/restore", response_model=DiaryDetailResponse)
async def restore_diary(
    diary_id: int,
    user_id: int = Depends(authenticate),
    diary_repo: DiaryRepository = Depends(),
) -> Diary:
    restored_diary = await diary_repo.restore_diary(diary_id=diary_id, user_id=user_id)

    if not restored_diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diary not found or cannot be restored",
        )

    return DiaryDetailResponse.model_validate(restored_diary)  # type: ignore


@router.post(
    path="/{diary_id}/analysis",
    summary="일기 감정 분석 및 조언 생성",
    status_code=status.HTTP_200_OK,
    response_model=DiaryAnalysisResponse,
)
async def analyze_diary(
        diary_id: int = Path(...),
        user_id: int = Depends(authenticate),
        diary_repo: DiaryRepository = Depends(),
        ai_service: AIAnalysisService = Depends(),
) -> DiaryAnalysisResponse:
    diary = await diary_repo.get_diary_detail(diary_id=diary_id)

    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일기를 찾을 수 없습니다."
        )

    if diary.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 일기만 분석할 수 있습니다."
        )

    # 토큰 사용량 최적화를 위한 텍스트 전처리
    content = diary.content[:1000]  # 최대 1000자로 제한

    try:
        analysis = await ai_service.analyze_diary_entry(content)
        return DiaryAnalysisResponse(
            diary_id=diary.id,
            mood_analysis=analysis.mood_analysis,
            emotional_insights=analysis.emotional_insights,
            advice=analysis.advice
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="일시적인 서비스 오류입니다."
        )