import os
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
from src.ex_diary.schema.response import ExDiaryListResponse, ExDiaryResponse
from src.friend.models import Friend
from src.friend.repository import FriendRepository
from src.user.service.authentication import authenticate
from src.user.schema.response import BasicResponse

router = APIRouter(prefix="/ex_diary", tags=["Exchange Diary"])
settings = Settings()


# 교환일기 작성 시 친구테이블에서 교환일기 수 증가하게 해야함, 마지막 교환 일자 업데이트도
@router.post(
    path="/{friend_id}",
    summary="교환일기 작성",
    response_model=BasicResponse,
    status_code=status.HTTP_201_CREATED,
)
async def write_ex_diary(
    friend_id: int = Path(..., description="친구 관계 id(친구의 유저 id(X))"),
    user_id: int = Depends(authenticate),
    title: str = Form(...),
    write_date: date = Form(...),
    weather: WeatherEnum = Form(...),
    mood: MoodEnum = Form(...),
    content: str = Form(...),
    image: Union[UploadFile, str] = File(default=None),
    ex_diary_repo: ExDiaryRepository = Depends(),  # 수정된 부분
    friend_repo: FriendRepository = Depends(),  # 수정된 부분
) -> BasicResponse:
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
                return BasicResponse(
                    message="이미지 파일이 비어있습니다.",
                    status="warning"
                )

            # 고유한 파일명 생성
            image_filename = f"ex_diary_{user_id}_{uuid.uuid4()}{os.path.splitext(image.filename)[1]}"  # type: ignore

            # S3에 업로드
            s3_key = f"ex_diaries/{image_filename}"
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

        # Friend 테이블 업데이트는 여기에 추가
        await friend_repo.update(
            friend_id=friend_id,
            data={
                "ex_diary_cnt": Friend.ex_diary_cnt + 1,
                "last_ex_date": datetime.now(),
            },
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return BasicResponse(
        message="일기가 성공적으로 생성되었습니다.",
        status="success"
    )


@router.get(
    path="/{friend_id}",
    summary="교환일기 목록 조회",
    status_code=status.HTTP_200_OK,
    response_model=ExDiaryListResponse,
)
async def ex_diary_list(
    friend_id: int = Path(..., description="친구 관계 id(친구의 유저 id (X))"),
    user_id: int = Depends(authenticate),
    ex_diary_repo: ExDiaryRepository = Depends(),
) -> ExDiaryListResponse:
    ex_diaries = await ex_diary_repo.get_ex_diary_list(friend_id)

    if not ex_diaries:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message": "검색 결과가 없습니다.",
                "status": "success",
            },
        )

    # return ex_diaries  # type: ignore
    return ExDiaryListResponse.build(ex_diaries=ex_diaries, user_id=user_id)


@router.get(
    path="/{friend_id}/{ex_diary_id}",
    summary="교환일기 상세 조회",
    status_code=status.HTTP_200_OK,
    response_model=ExDiaryResponse,
)
async def ex_diary_detail(
    user_id: int = Depends(authenticate),
    friend_id: int = Path(..., description="친구 관계 id(친구의 유저 id (X))"),
    ex_diary_id: int = Path(..., description="상세 조회할 교환일기의 id"),
    ex_diary_repo: ExDiaryRepository = Depends(),
) -> ExDiaryResponse:
    ex_diary = await ex_diary_repo.get_ex_diary_detail(
        friend_id=friend_id, ex_diary_id=ex_diary_id
    )

    if not ex_diary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "message": "해당 교환일기를 찾을 수 없습니다.",
                "status": "fail",
            },
        )

    return ExDiaryResponse.build(ex_diary=ex_diary, user_id=user_id)


@router.delete(
    path="/{friend_id}/{ex_diary_id}",
    summary="교환일기 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def ex_diary_delete(
        user_id: int = Depends(authenticate),
        friend_id: int = Path(..., description="친구 관계 id(친구의 유저 id (X))"),
        ex_diary_id: int = Path(..., description="삭제할 교환일기 id"),
        ex_diary_repo: ExDiaryRepository = Depends(),
        friend_repo: FriendRepository = Depends(),
) -> None:
    # S3 클라이언트 설정
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    # 삭제할 일기 정보 조회
    ex_diary = await ex_diary_repo.get_ex_diary_detail(
        friend_id=friend_id,
        ex_diary_id=ex_diary_id
    )

    # S3에 이미지가 있다면 삭제
    if ex_diary.img_url:
        try:
            # S3 키 추출 (URL에서 버킷명과 키 분리)
            s3_key = ex_diary.img_url.split(f"{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]

            # S3에서 이미지 삭제
            s3_client.delete_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=s3_key
            )
        except Exception as e:
            # S3 삭제 실패해도 로깅하고 진행
            print(f"S3 이미지 삭제 실패: {str(e)}")

    # 일기 삭제
    await ex_diary_repo.delete_ex_diary(
        user_id=user_id,
        friend_id=friend_id,
        ex_diary_id=ex_diary_id
    )

    # Friend 테이블 업데이트
    await friend_repo.update(
        friend_id=friend_id,
        data={
            "ex_diary_cnt": Friend.ex_diary_cnt - 1,
        },
    )
