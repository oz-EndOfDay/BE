from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.config.database.connection import get_async_session
from src.user.models import User
from src.user.repository import UserRepository
from src.user.schema.request import CreateRequestBody, UpdateRequestBody
from src.user.schema.response import JWTResponse, UserMeResponse
from src.user.service.authentication import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate,
    decode_access_token,
    encode_access_token,
    hash_password,
    verify_password,
)

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
router = APIRouter(prefix="/users", tags=["User"])


@router.post("/", response_model=UserMeResponse, status_code=201)
async def create_user(
    user_data: CreateRequestBody, session: AsyncSession = Depends(get_async_session)
) -> UserMeResponse:
    user_repo = UserRepository(session)  # UserRepository 인스턴스 생성

    # Pydantic 모델을 사용하여 사용자 객체 생성
    new_user = User(
        name=user_data.name,
        nickname=user_data.nickname,
        email=user_data.email,
        password=hash_password(user_data.password),  # 비밀번호 해싱 처리
    )

    created_user = await user_repo.create_user(new_user)  # 올바른 메서드 호출

    return UserMeResponse(
        id=created_user.id,
        name=created_user.name,
        nickname=created_user.nickname,
        email=created_user.email,
    )


# 로그인 엔드포인트 구현 (비동기)
@router.post(
    "/login",
    response_model=JWTResponse,
    status_code=status.HTTP_200_OK,
)
async def login_handler(
    email: str,
    password: str,
    session: AsyncSession = Depends(get_async_session),
) -> JWTResponse:
    result = await session.execute(select(User).filter(User.email == email))
    user: User | None = result.scalars().first()

    if user is not None and user.id is not None:
        if verify_password(plain_password=password, hashed_password=user.password):
            return JWTResponse(
                access_token=encode_access_token(user_id=user.id),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )


# 로그아웃 엔드포인트
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_handler(
    access_token: str, session: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:
    try:
        # JWT 토큰 디코딩
        payload = decode_access_token(access_token)
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # 토큰을 블랙리스트에 추가 추후에 블랙리스트 테이블 만들어서 작업

        return {"detail": "Successfully logged out"}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@router.put(path="/", status_code=status.HTTP_200_OK, response_model=UserMeResponse)
async def update_user(
    user_data: UpdateRequestBody,  # 사용자 수정 데이터에 대한 Pydantic 모델
    user_id: int = Depends(authenticate),  # 인증된 사용자 ID
    session: AsyncSession = Depends(get_async_session),
) -> UserMeResponse:
    user_repo = UserRepository(session)  # UserRepository 인스턴스 생성

    # 데이터베이스에서 사용자를 조회
    existing_user = await user_repo.get_user_by_id(user_id)

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

        # ID 확인
    if existing_user.id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User ID is invalid"
        )

    # 사용자 정보 업데이트
    existing_user.name = user_data.name if user_data.name else existing_user.name
    existing_user.nickname = (
        user_data.nickname if user_data.nickname else existing_user.nickname
    )
    existing_user.email = user_data.email if user_data.email else existing_user.email
    existing_user.img_url = (
        user_data.img_url if user_data.img_url else existing_user.img_url
    )
    existing_user.introduce = (
        user_data.introduce if user_data.introduce else existing_user.introduce
    )
    existing_user.modified_at = datetime.utcnow()

    # 비밀번호가 제공된 경우에만 해싱하여 업데이트
    if user_data.password:
        existing_user.password = hash_password(user_data.password)

    # 사용자 정보 저장
    await user_repo.update_user(existing_user.id, existing_user.__dict__)

    return UserMeResponse(
        id=existing_user.id,
        name=existing_user.name,
        nickname=existing_user.nickname,
        email=existing_user.email,
        modified_at=existing_user.modified_at,
    )


# soft delete 방식으로 삭제 일자를 db에 입력 후 7일 지난 데이터는 안보이도록 함.
@router.delete(path="/delete", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    user_repo = UserRepository(session)
    await user_repo.soft_delete_user(user_id)

    return {
        "message": "회원탈퇴가 처리되었습니다. 데이터는 7일간 보관됩니다.",
        "status": "success",
    }
