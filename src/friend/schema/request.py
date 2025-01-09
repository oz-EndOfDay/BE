from pydantic import BaseModel, EmailStr


class FriendRequest(BaseModel):
    user_id1: int
    user_id2: int


class FriendRequestByEmail(BaseModel):
    email: EmailStr  # 친구 신청을 보낼 사용자의 이메일


class AcceptFriendRequest(BaseModel):
    friend_request_id: int


class DeleteFriendRequest(BaseModel):
    friend_delete_id: int  # 삭제할 친구 관계의 ID
