from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.friend.repository import FriendRepository
from src.friend.schema.request import (
    AcceptFriendRequest,
    DeleteFriendRequest,
    FriendRequestByEmail,
)
from src.friend.schema.response import (
    DeleteFriendResponse,
    FriendRequestByEmailResponse,
    FriendRequestResponse,
    FriendRequestsListResponse,
    FriendResponse,
    FriendsListResponse,
)
from src.notification.models import Notification
from src.notification.repository import NotificationRepository
from src.notification.service.websocket import manager
from src.user.repository import UserRepository
from src.user.service.authentication import authenticate

router = APIRouter(prefix="/friends", tags=["Friend"])


@router.post(
    "/{user_id}",
    summary="친구 신청 (검색된 친구에서 친구 id 값을 담아 요청)",
    response_model=FriendRequestByEmailResponse,
)
async def send_friend_request_by_id(
    user_id: int,
    current_user_id: int = Depends(authenticate),  # 현재 인증된 사용자의 ID
    session: AsyncSession = Depends(get_async_session),
) -> FriendRequestByEmailResponse:
    user_repo = UserRepository(session)
    friend_repo = FriendRepository(session)
    current_user = await user_repo.get_user_by_id(current_user_id)
    target_user = await user_repo.get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(
            status_code=404, detail="해당 메일을 가진 사용자가 없습니다."
        )

    aleady_friend = await friend_repo.check_friendship(current_user_id, target_user.id)
    if aleady_friend:
        if aleady_friend.is_accept:
            raise HTTPException(status_code=400, detail="이미 친구 관계입니다.")
        else:
            raise HTTPException(status_code=400, detail="이미 친구 신청을 보냈습니다.")

    if target_user.id == current_user_id:
        raise HTTPException(status_code=400, detail="자신을 친구로 등록할 수 없습니다.")


    # 친구 신청 생성
    try:
        if not current_user:
            raise HTTPException(
                status_code=400, detail="보내는 사용자 정보가 없습니다."
            )
        message = f"{current_user.nickname} 님이 친구요청을 보내셨습니다."
        notification = Notification(
            user_id=target_user.id, title="친구 요청", message=message
        )

        noti_repo = NotificationRepository(session)
        noti_info = await noti_repo.create_notification(notification)

        await manager.send_personal_message(
            message="새로운 알림이 있습니다.",
            user_id=target_user.id,
            noti_id=noti_info.id
        )

        await friend_repo.create_friend_request(current_user_id, target_user.id)
        return FriendRequestByEmailResponse(success=True, message="친구 신청 완료.")
    except Exception as e:
        raise HTTPException(status_code=500, detail="친구 신청 실패.")


@router.get(
    "/get_request",
    summary="받은 친구 요청 리스트 조회",
    response_model=FriendRequestsListResponse,
)
async def list_get_friend_requests(
    current_user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> FriendRequestsListResponse:
    frd_repo = FriendRepository(session)

    get_requests = await frd_repo.get_friend_request_list(current_user_id)

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
            for request in get_requests
            if request is not None
        ]
    )


@router.get(
    "/send_request",
    summary="보낸 친구 요청 리스트 조회",
    response_model=FriendRequestsListResponse,
)
async def list_sent_friend_requests(
    current_user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> FriendRequestsListResponse:
    frd_repo = FriendRepository(session)

    sent_requests = await frd_repo.sent_friend_request_list(current_user_id)

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


@router.patch("/{friend_id}", summary="내가 받은 친구 요청 수락")
async def accept_friend(
    friend_id: int,
    current_user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, str]:
    frd_repo = FriendRepository(session)

    try:
        accept_request = await frd_repo.accept_friend_request(
            current_user_id, friend_id
        )
        if accept_request:
            return {"success": "친구 수락."}
        else:
            return {"failed": "요청한 사용자를 찾을 수 없습니다."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", summary="친구 목록 조회", response_model=FriendsListResponse)
async def list_friends(
    current_user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> FriendsListResponse:
    frd_repo = FriendRepository(session)
    friends = await frd_repo.get_friends(current_user_id)
    return FriendsListResponse(
        friends=[FriendResponse.model_validate(friend) for friend in friends]
    )


# 친구 거절 시에도 테이블에서 삭제 동작하게 함.
@router.delete("/{friend_id}", summary="친구 삭제", response_model=DeleteFriendResponse)
async def delete_friend(
    friend_id: int,
    current_user_id: int = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session),
) -> DeleteFriendResponse:
    frd_repo = FriendRepository(session)

    success = await frd_repo.delete_friend(current_user_id, friend_id)

    if success:
        return DeleteFriendResponse(
            success=True, message="친구 삭제가 완료 되었습니다."
        )
    else:
        raise HTTPException(status_code=404, detail="친구 관계가 아닙니다.")
