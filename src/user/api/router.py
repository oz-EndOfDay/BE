# from fastapi import APIRouter, Depends, status
# from fastapi.security import OAuth2PasswordRequestForm
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from src.config.database.connection import get_async_session
# from src.user.models import User
# from src.user.schema.request import CreateRequestBody
#
# router = APIRouter(prefix="/users", tags=["User"])
#
#
# @router.post(path="", status_code=status.HTTP_201_CREATED)
# async def create_user(
#     body: CreateRequestBody, session: AsyncSession = Depends(get_async_session)
# ) -> tuple[int, dict[str, str]]:
#     new_user = User.create(
#         name=body.name,
#         nickname=body.nickname,
#         email=body.email,
#         password=body.password,
#     )
#
#     session.add(new_user)
#     await session.commit()
#
#     return 201, {
#         "message": "회원가입이 성공적으로 처리되었습니다.",
#         "status": "success",
#     }
#
# @router.post(path="/login", status_code=status.HTTP_202_ACCEPTED)
# async def login(form_data: OAuth2PasswordRequestForm = Depends()):
