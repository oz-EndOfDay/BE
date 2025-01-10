import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, Dict, TypedDict, cast

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from passlib.context import CryptContext
from starlette import status

from src.config import Settings

settings = Settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 비밀번호 해싱 함수
def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


# 비밀번호 적합성 검사
# passlib의 CryptContext에서 내부적으로 salt 생성처리(salt 는 미리 계산된 해시값 테이블 공격 방지, 같은 비밀번호 사용자도 다른 해시값을 갖게함.
def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if hashed_password is None:
        return False
    return cast(bool, pwd_context.verify(plain_password, hashed_password))


# jwt 인증 관련
class JWTPayload(TypedDict):
    user_id: int
    isa: int


def encode_access_token(user_id: int) -> str:
    payload: JWTPayload = {
        "user_id": user_id,
        "isa": int(time.time()),
    }
    access_token: str = jwt.encode(
        cast(dict[str, Any], payload), SECRET_KEY, algorithm=ALGORITHM
    )
    return access_token


def encode_refresh_token(user_id: int) -> str:
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "iat": int(time.time()),
        "exp": int(time.time())
        + (REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60),  # 30일 후 만료
        "type": "refresh",
    }
    refresh_token: str = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return refresh_token


# def decode_access_token(access_token: str) -> JWTPayload:
#     return cast(
#         JWTPayload, jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
#     )
def decode_access_token(access_token: str) -> JWTPayload:
    try:
        # 엄격한 디코딩 검증
        payload = jwt.decode(
            access_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": True, "require_exp": True, "verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        # 토큰 만료 처리
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        # 토큰 유효성 검증 실패
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


def decode_refresh_token(refresh_token: str) -> JWTPayload:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return cast(JWTPayload, payload)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


def refresh_access_token(refresh_token: str) -> str:
    try:
        # 리프레시 토큰 디코딩 및 유효성 검사
        payload = decode_refresh_token(refresh_token)
        user_id = payload["user_id"]

        # 새로운 액세스 토큰 발급
        new_access_token = encode_access_token(user_id)
        return new_access_token

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


def authenticate(
    auth_header: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    refresh_token: str = Depends(HTTPBearer()),
) -> int:
    try:
        # 인증 성공
        payload: JWTPayload = decode_access_token(access_token=auth_header.credentials)

        # token 만료 검사
        expiry_seconds = 60 * 60 * 24 * 7
        if payload["isa"] + expiry_seconds < time.time():
            # 액세스 토큰이 만료된 경우 리프레시 토큰으로 새로운 액세스 토큰 발급
            refresh_access_token(refresh_token)
            return payload["user_id"]  # 또는 사용자 ID를 반환할 수 있음

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    return payload["user_id"]


def create_verification_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.now() + timedelta(hours=1),  # 1시간 후 만료
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# 임시비밀번호 랜덤 생성기 ( 8자리 )
def generate_password() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))
