import random
import string
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, TypedDict, cast

import jwt
from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer
from jose import JWTError
from passlib.context import CryptContext
from starlette import status

from src.config import Settings

settings = Settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
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
    exp: int


def encode_access_token(user_id: int) -> str:
    payload: JWTPayload = {
        "user_id": user_id,
        "isa": int(time.time()),
        "exp": int(time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60),
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


def decode_access_token(access_token: str) -> JWTPayload:
    return cast(
        JWTPayload, jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    )


# def decode_access_token(access_token: str) -> JWTPayload:
#     try:
#         # 엄격한 디코딩 검증
#         payload = jwt.decode(
#             access_token,
#             SECRET_KEY,
#             algorithms=[ALGORITHM],
#             options={"verify_signature": True, "require_exp": True, "verify_exp": True},
#         )
#         return payload
#     except jwt.ExpiredSignatureError:
#         # 토큰 만료 처리
#         raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
#     except jwt.InvalidTokenError:
#         # 토큰 유효성 검증 실패
#         raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")


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


# 액세스 토큰 재발급
def refresh_access_token(refresh_token: str = Depends(HTTPBearer())) -> str:
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


# fresh token 만료 확인
def is_refresh_token_expired(
    refresh_token: str = Depends(HTTPBearer()),
) -> bool:
    try:
        # 토큰 디코딩
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        # 만료 시간 확인 (exp 필드 존재 여부 확인)
        if "exp" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid (missing expiry).",
            )

        # 현재 시간과 만료 시간 비교
        current_time = int(time.time())
        if payload["exp"] < current_time:
            return True  # 만료됨
        return False  # 유효함

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token."
        )


def authenticate(
    request: Request,
    response: Response,
) -> int:
    access_token = request.headers.get("Authorization", "").replace("Bearer ", "")
    refresh_token = request.headers.get("Refresh-Token", "")

    if not access_token:
        if not refresh_token:
            raise HTTPException(status_code=401, detail="로그인 필요")

        # 리프레시 토큰 유효성 추가 검증
        if is_refresh_token_expired(refresh_token):
            raise HTTPException(status_code=401, detail="다시 로그인")

        try:
            payload = decode_refresh_token(refresh_token)
            new_access_token = encode_access_token(payload["user_id"])

            # 헤더에 새 액세스 토큰 설정
            response.headers["Authorization"] = f"Bearer {new_access_token}"

            return payload["user_id"]

        except JWTError:
            raise HTTPException(status_code=401, detail="인증 실패")

    try:
        payload = decode_access_token(access_token)
        return payload["user_id"]

    except JWTError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰")


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
