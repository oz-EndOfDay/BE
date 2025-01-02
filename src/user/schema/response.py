from pydantic import BaseModel, ConfigDict

class UserMeResponse(BaseModel):  # 내 정보를 반환할 때
    id: int | None = None
    name: str | None = None
    nickname: str | None = None

    model_config = ConfigDict(from_attributes=True)


class JWTResponse(BaseModel):
    access_token: str
