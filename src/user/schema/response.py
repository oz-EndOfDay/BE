from pydantic import BaseModel, ConfigDict


# 내 정보 조회
class UserMeResponse(BaseModel):
    id: int
    username: str
    email: str | None
    password: str

    model_config = ConfigDict(from_attributes=True)


# 다른 사람의 정보 조회
class UserResponse(BaseModel):
    username: str


class JWTResponse(BaseModel):
    access_token: str
