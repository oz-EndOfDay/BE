import uuid
from datetime import datetime
from typing import Dict

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import Settings
from src.config.database.connection import get_async_session
from src.user.models import User
from src.user.repository import UserRepository
from src.user.schema.request import CreateRequestBody, UpdateRequestBody
from src.user.schema.response import JWTResponse, UserMeResponse
from src.user.service.authentication import (
    ALGORITHM,
    authenticate,
    create_verification_token,
    decode_access_token,
    encode_access_token,
    hash_password,
    verify_password,
)
from src.user.service.smtp import send_email

settings = Settings()

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

    # 인증 토큰 생성
    token = create_verification_token(user_data.email)
    # 인증 링크 생성
    verification_link = f"http://localhost:8000/users/email_verify/{token}"

    await send_email(
        to=user_data.email,
        subject="Email Verification",
        body=f"Please verify your email by clicking the following link: {verification_link}",
    )

    return UserMeResponse(
        id=created_user.id,
        name=created_user.name,
        nickname=created_user.nickname,
    )


# 회원가입 이메일 인증
@router.get("/email_verify/{token}")
async def verify_email(
    token: str, session: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("email")

        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")

        user_repo = UserRepository(session)
        user = await user_repo.get_user_by_email(email)  # 이메일로 사용자 조회

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_active = True

        if user.id is None:
            raise HTTPException(status_code=400, detail="User ID is invalid")
        await user_repo.update_user(user.id, user.__dict__)

        return {"message": "Email verified successfully!"}

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")

    except jwt.PyJWTError:
        raise HTTPException(status_code=400, detail="Invalid token")


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
    existing_user.img_url = (
        user_data.img_url if user_data.img_url else existing_user.img_url
    )
    existing_user.introduce = (
        user_data.introduce if user_data.introduce else existing_user.introduce
    )
    existing_user.modified_at = datetime.now()

    # 비밀번호가 제공된 경우에만 해싱하여 업데이트
    if user_data.password:
        existing_user.password = hash_password(user_data.password)

    # 사용자 정보 저장
    await user_repo.update_user(existing_user.id, existing_user.__dict__)

    return UserMeResponse(
        id=existing_user.id,
        name=existing_user.name,
        nickname=existing_user.nickname,
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
