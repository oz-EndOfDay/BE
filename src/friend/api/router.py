from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.friend.models import Friend
from src.friend.repository import FriendRepository
from src.friend.schema.request import AcceptFriendRequest, FriendRequest
from src.friend.schema.response import FriendResponse

router = APIRouter(prefix="/friends", tags=["Friend"])


@router.post("/", response_model=FriendResponse)
async def send_friend_request(
    request: FriendRequest, session: AsyncSession = Depends(get_async_session)
) -> Friend:
    frd_repo = FriendRepository(session)
    friend_request = await frd_repo.create_friend_request(
        request.user_id1, request.user_id2
    )
    return friend_request


@router.post("/accept", response_model=FriendResponse)
async def accept_friend(
    request: AcceptFriendRequest, session: AsyncSession = Depends(get_async_session)
) -> Friend:
    try:
        frd_repo = FriendRepository(session)
        accepted_friend = await frd_repo.accept_friend_request(
            request.friend_request_id
        )
        return accepted_friend
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
