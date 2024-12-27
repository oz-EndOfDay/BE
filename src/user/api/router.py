from fastapi import APIRouter, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database.connection import get_async_session
from src.user.schema.request import CreateRequestBody
from src.user.models import User

router = APIRouter(prefix="/users", tags=["User"])


@router.post(path="/create", status_code=status.HTTP_201_CREATED)
async def create_user(body: CreateRequestBody, session: AsyncSession = Depends(get_async_session)):
    new_user = User.create(
        name=body.name,
        nickname=body.nickname,
        email=body.email,
        password=body.password,
    )

    session.add(new_user)
    await session.commit()

    return 201, {"message": "회원가입이 성공적으로 처리되었습니다.", "status": "success"}