from pydantic import BaseModel, ConfigDict


class UserMeResponse(BaseModel):        # 내 정보를 반환할 때
    id: int
    username: str
    email: str | None
    password: str

    model_config = ConfigDict(from_attributes=True)