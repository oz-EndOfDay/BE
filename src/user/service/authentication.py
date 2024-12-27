import time
from typing import TypedDict

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


# password
def hash_password(plain_text: str) -> str:
    hashed_password_bytes: bytes = bcrypt.hashpw(
        plain_text.encode("utf-8"), bcrypt.gensalt()
    )

    return hashed_password_bytes.decode("utf-8")


def check_password(plain_text: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_text.encode("utf-8"), hashed_password.encode("utf-8")
    )

# JWT
SECRET_KEY = "92424d57e87900cd12b3f8ae43d31a0bfcbd34ea1b0004767ad0f61ab8376803"
ALGORITHM = "HS256"

class JWTPayLoad(TypedDict):
    user_id: int
    isa: int

def encode_access_token(user_id: int) -> str:
    payload: JWTPayLoad = {"user_id": user_id, "isa": int(time.time())}
    access_token: str = jwt.encode(
        payload, SECRET_KEY, algorithm=ALGORITHM
    )

    return access_token

def decode_access_token(access_token: str) -> JWTPayLoad:
    return jwt.decode(
        access_token, SECRET_KEY, algorithms=[ALGORITHM]
    )

def authenticate(
        auth_header: HTTPAuthorizationCredentials = Depends(HTTPBearer())
) -> int:
    payload: JWTPayLoad = decode_access_token(auth_header.credentials)

    # token 만료 검사
    EXPIRY_SECONDS = 60 * 60 * 24 * 7
    if payload["isa"] + EXPIRY_SECONDS < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    return payload["user_id"]