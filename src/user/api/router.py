from datetime import datetime
from typing import Dict

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from blacklist import blacklist_token
from src.config import Settings
from src.config.database.connection import get_async_session
from src.user.models import User
from src.user.repository import UserNotFoundException, UserRepository
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

# 유저 생성 (회원가입)
@router.post("/", response_model=UserMeResponse, status_code=201)
async def create_user(
    user_data: CreateRequestBody, session: AsyncSession = Depends(get_async_session)
) -> UserMeResponse:
    user_repo = UserRepository(session)  # UserRepository 인스턴스 생성

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

# 패스워드 분실
@router.get("/forgot_password")
async def forgot_password(
    email: str, session: AsyncSession = Depends(get_async_session)
) -> Dict[str, str]:

    user_repo = UserRepository(session)
    temp_password = await user_repo.forgot_password(email)

    await send_email(
        to=email,
        subject="Forgot Password",
        body=f"Your temporary password is {temp_password}. Please change your password after logging in with your temporary password.",
    )

    return {"Message": "Temporary password has been sent your mail."}


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

        if user is None:
            raise HTTPException(status_code=404, detail="Email not found")

        update_data = UpdateRequestBody(is_active=True, modified_at=datetime.now())

        if not user.id is None:
            await user_repo.update_user(user.id, update_data)

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
    response: Response,
    session: AsyncSession = Depends(get_async_session),
) -> JWTResponse:
    user_repo = UserRepository(session)
    user = await user_repo.get_user_by_email(email)

    if user is not None and user.id is not None:
        if user.is_active:
            if verify_password(plain_password=password, hashed_password=user.password):
                access_token = encode_access_token(user_id=user.id)
                response.set_cookie(
                    key="access_token", value=access_token, httponly=True
                )
                print(response)
                return JWTResponse(
                    access_token=access_token,
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please check your email to complete email verification.",
        )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found",
    )

# 로그아웃 엔드포인트
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_handler(request: Request) -> Dict[str, str]:
    try:
        access_token = request.cookies.get("access_token")
        if access_token is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="No token provided"
            )
        # JWT 토큰 디코딩
        payload = decode_access_token(access_token)
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # 토큰을 블랙리스트에 추가하는 기능 필요
        await blacklist_token(access_token)
        return {"detail": "Successfully logged out"}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

# 사용자 정보 수정
@router.put(path="/", status_code=status.HTTP_200_OK, response_model=UserMeResponse)
async def update_user(
    user_data: UpdateRequestBody,  # 사용자 수정 데이터에 대한 Pydantic 모델
    user_id: int = Depends(authenticate),  # 인증된 사용자 ID
    session: AsyncSession = Depends(get_async_session),
) -> UserMeResponse:
    user_repo = UserRepository(session)  # UserRepository 인스턴스 생성

    try:
        updated_user = await user_repo.update_user(user_id, user_data)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserMeResponse(
        id=updated_user.id,
        name=updated_user.name,
        nickname=updated_user.nickname,
    )


# soft delete 방식으로 삭제 일자를 db에 입력 후 7일 지난 데이터는 안보이도록 함.
@router.delete(path="/delete", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    user_repo = UserRepository(session)
    try:
        await user_repo.soft_delete_user(user_id)
    except UserNotFoundException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {
        "message": "회원탈퇴가 처리되었습니다. 데이터는 7일간 보관됩니다.",
        "status": "success",
    }
