import logging
import os
import uuid
from datetime import date, datetime
from typing import Dict, Optional, Union

import boto3
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
    MoodStatisticsResponse,
)
from src.diary.service.AIAnalysis import analyze_diary_entry
from src.user.schema.response import BasicResponse
from src.user.service.authentication import authenticate

router = APIRouter(prefix="/diary", tags=["Diary"])
settings = Settings()

logger = logging.getLogger(__name__)


@router.post(
    path="",
    summary="일기 작성",
    response_model=BasicResponse,
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
) -> BasicResponse:
    # S3 클라이언트 설정
    # s3_client = boto3.client(
    #     "s3",
    #     aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    #     aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    #     region_name=settings.AWS_REGION,
    # )
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.NCP_ACCESS_KEY,
        aws_secret_access_key=settings.NCP_SECRET_KEY,
        endpoint_url=settings.NCP_ENDPOINT_URL,
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
                return BasicResponse(
                    message="이미지 파일이 비어있습니다.",
                    status="warning",
                )

            # 고유한 파일명 생성
            image_filename = f"diary_{user_id}_{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"  # type: ignore

            # S3에 업로드
            s3_key = f"diaries/{image_filename}"
            # s3_client.upload_fileobj(
            #     image.file,  # type: ignore
            #     settings.S3_BUCKET_NAME,
            #     s3_key,
            #     ExtraArgs={"ContentType": image.content_type},  # type: ignore
            # )
            s3_client.upload_fileobj(
                image.file,  # type: ignore
                settings.NCP_BUCKET_NAME,
                s3_key,
                ExtraArgs={'ACL': 'public-read'},  # type: ignore
            )

            # 공개 URL 생성
            # img_url = f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"
            img_url = f"{settings.NCP_ENDPOINT_URL}/{settings.NCP_BUCKET_NAME}/{s3_key}"

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

    return BasicResponse(
        message="일기가 성공적으로 생성되었습니다.",
        status="success",
    )


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
    path="/mood-stats",
    summary="사용자의 기분 통계 조회",
    response_model=MoodStatisticsResponse,
    status_code=status.HTTP_200_OK,
)
async def get_mood_statistics(
    user_id: int = Depends(authenticate),
    diary_repo: DiaryRepository = Depends(),
) -> MoodStatisticsResponse:
    """
    사용자가 작성한 일기들에서 기분별 개수를 반환합니다.
    """
    try:
        # 사용자의 모든 일기를 가져오기
        user_diaries = await diary_repo.get_all_by_user(user_id)

        # 기분별 개수 집계
        mood_stats = {mood: 0 for mood in MoodEnum}
        for diary in user_diaries:
            mood_stats[diary.mood] += 1

        return MoodStatisticsResponse.build(mood_stats=mood_stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 계산 중 오류 발생: {str(e)}")


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
)
async def delete_diary(
    diary_id: int,
    user_id: int = Depends(authenticate),
    diary_repo: DiaryRepository = Depends(),
) -> None:

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
    # return BasicResponse(message="Diary entry successfully deleted.", status="success")


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
) -> DiaryAnalysisResponse:
    diary = await diary_repo.get_diary_detail(diary_id=diary_id)

    if not diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="일기를 찾을 수 없습니다."
        )

    if diary.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 일기만 분석할 수 있습니다.",
        )

    try:
        # diary.content가 None일 가능성을 대비해 처리
        diary_content = diary.content or ""
        analysis_result = analyze_diary_entry(diary_content)
        diary_analysis_result = analysis_result.split("---")[0]
        advice_analysis_result = analysis_result.split("---")[1]

        return DiaryAnalysisResponse(
            diary_id=diary_id,
            # diary_content=diary_content,      # 반환 시 일기 내용은 반환하지 않음
            diary_analysis_result=diary_analysis_result,
            advice_analysis_result=advice_analysis_result,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="일시적인 서비스 오류입니다.",
        )
