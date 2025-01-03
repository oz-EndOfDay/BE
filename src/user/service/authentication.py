import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, TypedDict, cast

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from starlette import status

from config import Settings

settings = Settings()

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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


def decode_access_token(access_token: str) -> JWTPayload:
    return cast(
        JWTPayload, jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
    )


def authenticate(
    auth_header: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> int:
    # 인증 성공
    payload: JWTPayload = decode_access_token(access_token=auth_header.credentials)

    # token 만료 검사
    expiry_seconds = 60 * 60 * 24 * 7
    if payload["isa"] + expiry_seconds < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
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
