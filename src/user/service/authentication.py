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
    return bcrypt.checkpw(plain_text.encode("utf-8"), hashed_password.encode("utf-8"))


# JWT
SECRET_KEY = "f3d7522be0fbcf3b7fe72edf628fd6cf9eddd93e4f9d2bee32cfd5ea8bb83486"
ALGORITHM = "HS256"


class JWTPayload(TypedDict):
    user_id: int
    isa: int
