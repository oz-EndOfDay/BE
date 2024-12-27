from typing import Dict

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.config.database.connection import get_session
from src.user.models import User
from src.user.schema.request import CreateUserRequestBody

router = APIRouter(prefix="/user", tags=["user"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    body: CreateUserRequestBody,
    session: AsyncSession = Depends(get_session),
) -> Dict[str, str]:

    new_user = User.create(
        name=body.name, nickname=body.nickname, password=body.password, email=body.email
    )
    session.add(new_user)
    await session.commit()  # db 저장

    return {"message": "User created successfully."}


__all__ = ["router"]
