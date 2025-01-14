from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class FriendCreate(BaseModel):
    user_id1: int
    user_id2: int


class FriendRequestByEmailResponse(BaseModel):
    success: bool
    message: str


class FriendRequestResponse(BaseModel):
    id: Optional[int]
    user_id1: Optional[int]
    user_id2: Optional[int]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class FriendRequestsListResponse(BaseModel):
    sent_requests: list[FriendRequestResponse]


class FriendResponse(BaseModel):
    id: Optional[int]  # 요청 ID
    user_id1: Optional[int]  # 요청한 사용자 ID
    user_id2: Optional[int]  # 요청받은 사용자 ID
    is_accept: Optional[bool]  # 수락 여부
    ex_diary_cnt: Optional[int]  # 일기 수
    last_ex_date: Optional[datetime]  # 마지막 교류 날짜 (Optional)
    created_at: Optional[datetime]  # 생성일

    class Config:
        from_attributes = True  # from_orm 대신 사용


class FriendListResponse(BaseModel):  # 친구 요청 목록을 보기 위한 모델
    friends: List[FriendResponse]

    class Config:
        from_attributes = True


class FriendsResponse(BaseModel):
    id: int
    is_accept: bool
    ex_diary_cnt: Optional[int]  # 예시로 친구 일기의 개수를 추가
    last_ex_date: Optional[datetime]  # 마지막 교류 날짜
    created_at: datetime
    user1_nickname: Optional[str]  # user1의 닉네임
    user2_nickname: Optional[str]  # user2의 닉네임

    class Config:
        from_attributes = True  # ORM 모델에서 Pydantic 모델로 변환을 쉽게 해줍니다.


# 친구 목록 전체를 감싸는 모델
class FriendsListResponse(BaseModel):
    friends: List[FriendsResponse]  # 친구 목록은 FriendsResponse 객체들로 이루어짐

    class Config:
        from_attributes = True  # ORM 모델에서 Pydantic 모델로 변환을 쉽게 해줍니다.


class DeleteFriendResponse(BaseModel):
    success: bool
    message: str
