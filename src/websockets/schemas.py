from datetime import datetime

from pydantic import BaseModel


class WebsocketCreate(BaseModel):
    message: str
    friend_id: int
    user_id: int


class WebsocketOut(BaseModel):
    message_id: int
    message: str
    created_at: datetime
    friend_id: int
    user_id: int

    class Config:
        orm_mode = True  # SQLAlchemy 모델을 그대로 사용할 수 있도록 설정
