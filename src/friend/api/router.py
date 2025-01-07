from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.friend.models import Friend
from src.friend.repository import FriendRepository
from src.friend.schema.request import AcceptFriendRequest, FriendRequest
from src.friend.schema.response import (
    FriendRequestResponse,
    FriendRequestsListResponse,
    FriendResponse,
    FriendsListResponse,
)
from src.user.service.authentication import authenticate

router = APIRouter(prefix="/friends", tags=["Friend"])


@router.post("/request", summary="친구 요청 보내기", response_model=FriendResponse)
async def send_friend_request(
    request: FriendRequest,
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> Friend:
    frd_repo = FriendRepository(session)
    friend_request = await frd_repo.create_friend_request(user_id, request.user_id2)
    return friend_request


@router.get(
    "/request",
    summary="친구 요청 리스트 조회",
    response_model=FriendRequestsListResponse,
)
async def list_sent_friend_requests(
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> FriendRequestsListResponse:
    frd_repo = FriendRepository(session)

    sent_requests = await frd_repo.get_friend_request_list(user_id)

    return FriendRequestsListResponse(
        sent_requests=[
            FriendRequestResponse(
                id=request.id if request.id is not None else 0,
                user_id1=request.user_id1 if request.user_id1 is not None else 0,
                user_id2=request.user_id2 if request.user_id2 is not None else 0,
                created_at=(
                    request.created_at
                    if request.created_at is not None
                    else datetime.now()
                ),
            )
            for request in sent_requests
            if request is not None
        ]
    )


@router.post("/accept", summary="친구 수락", response_model=FriendResponse)
async def accept_friend(
    request: AcceptFriendRequest,
    user_id: int = Depends(
        authenticate
    ),  # 인증된 사용자 ID 가져오기 (authenticate 함수 필요)
    session: AsyncSession = Depends(get_async_session),
) -> FriendResponse:
    frd_repo = FriendRepository(session)

    try:
        accept_request = await frd_repo.accept_friend_request(
            user_id, request.friend_request_id
        )

        return FriendResponse(
            id=accept_request.id,
            user_id1=accept_request.user_id1,
            user_id2=accept_request.user_id2,
            is_accept=accept_request.is_accept,
            ex_diary_cnt=accept_request.ex_diary_cnt,
            last_ex_date=accept_request.last_ex_date,
            created_at=accept_request.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/", summary="친구 목록 조회", response_model=FriendsListResponse)
async def list_friends(
    user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> FriendsListResponse:
    frd_repo = FriendRepository(session)
    friends = await frd_repo.get_friends(user_id)
    return FriendsListResponse(
        friends=[FriendResponse.model_validate(friend) for friend in friends]
    )
