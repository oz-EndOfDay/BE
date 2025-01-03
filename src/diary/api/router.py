import os
import shutil
from datetime import date

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

from diary.models import Diary, MoodEnum, WeatherEnum
from diary.repository import DiaryReqository
from diary.schema.response import DiaryDetailResponse, DiaryListResponse
from user.service.authentication import authenticate

router = APIRouter(prefix="/diary", tags=["Diary"])


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
    image: UploadFile | str = File(default=None),
    diary_repo: DiaryReqository = Depends(),
) -> tuple[int, dict[str, str]]:

    img_url: str | None = None

    if image and image.filename:  # type: ignore
        image_filename: str = f"{user_id}_diary_{image.filename}"  # type: ignore
        img_url = os.path.join("src/diary/img", image_filename)

        with open(img_url, "wb") as f:
            shutil.copyfileobj(image.file, f)  # type: ignore

    new_diary = await Diary.create(
        user_id=user_id,
        title=title,
        write_date=write_date,
        weather=weather,
        mood=mood,
        content=content,
        img_url=img_url or "",
    )

    try:
        await diary_repo.save(new_diary)
    except Exception as e:
        print(e)
        raise HTTPException(status_code=404, detail=str(e))

    return 201, {
        "message": "Your diary entry has been successfully created.",
        "status": "success",
    }


@router.get(
    path="",
    summary="전체 일기 조회",
    status_code=status.HTTP_200_OK,
    response_model=DiaryListResponse,
)
async def diary_list(  # 삭제 일기(7일 이내) 복구 api 필요, 사진 삭제 로직 필요, 유저 삭제 시 같이 삭제 필요, 제목/내용 및 년도/월 검색 기능 필요
    user_id: int = Depends(authenticate),
    diary_repo: DiaryReqository = Depends(),
) -> DiaryListResponse:

    diaries = await diary_repo.get_diary_list(user_id)

    if not diaries:
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail={
                "message": "You haven't written any diary entries yet.",
                "status": "success",
            },
        )

    return DiaryListResponse.build(diaries=list(diaries))


@router.get(
    path="/deleted",
    summary="삭제된 일기(7일 이내) 확인",
    status_code=status.HTTP_200_OK,
    response_model=DiaryListResponse,
)
async def diary_list_deleted(
    user_id: int = Depends(authenticate),
    diary_repo: DiaryReqository = Depends(),
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
    summary="일기(1개) 조회",
    status_code=status.HTTP_200_OK,
    response_model=DiaryDetailResponse,
)
async def diary_detail(
    diary_id: int = Path(..., description="조회할 일기의 고유 식별자"),
    user_id: int = Depends(authenticate),
    diary_repo: DiaryReqository = Depends(),
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

    return DiaryDetailResponse.model_validate(diary)


@router.delete(
    path="/{diary_id}",
    summary="선택한 일기 삭제",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_diary(
    diary_id: int,
    user_id: int = Depends(authenticate),
    diary_repo: DiaryReqository = Depends(),
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
