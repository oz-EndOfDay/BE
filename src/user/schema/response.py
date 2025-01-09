from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserMeResponse(BaseModel):  # 내 정보를 반환할 때
    id: int | None = None
    name: str | None = None
    nickname: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserMeDetailResponse(BaseModel):  # 내 정보를 반환할 때
    id: int | None = None
    name: str | None = None
    nickname: str | None = None
    email: str | None = None
    introduce: str | None = None
    img_url: str | None = None
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class JWTResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserSearchResponse(BaseModel):
    id: int
    nickname: str
    email: str

    class Config:
        from_attributes = True


class SocialUser(BaseModel):
    email: EmailStr
    nickname: str
    provider: str  # "kakao", "google" 등
    is_active: bool = True


class UserInfo(BaseModel):
    id: int
    nickname: str
    email: EmailStr
    connected_at: str
