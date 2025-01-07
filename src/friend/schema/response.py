from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class FriendCreate(BaseModel):
    user_id1: int
    user_id2: int


class FriendResponse(BaseModel):
    id: int
    user_id1: int
    user_id2: int
    is_accept: bool
    ex_diary_cnt: int
    last_ex_date: datetime | None
    created_at: datetime

    class Config:
        orm_mode = True


class FriendList(BaseModel):
    friends: List[FriendResponse]
