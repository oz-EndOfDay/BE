from pydantic import BaseModel


class FriendRequest(BaseModel):
    user_id1: int
    user_id2: int


class AcceptFriendRequest(BaseModel):
    friend_request_id: int
