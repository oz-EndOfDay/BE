from datetime import datetime

from pydantic import BaseModel


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    user_id: int
    friend_id: int


class MessageResponse(MessageBase):
    id: int
    user_id: int
    friend_id: int
    created_at: datetime

    class Config:
        from_attributes = True
