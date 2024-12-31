# from fastapi import HTTPException, status
# from sqlalchemy import Column, String, DateTime
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy.future import select
# from sqlalchemy.ext.declarative import declarative_base
# from datetime import datetime, timedelta
# from pydantic import BaseModel, Field
# 주석
# Base = declarative_base()
#
# class BlackListItem(BaseModel):
#     token: str = Field(..., description="블랙리스트에 추가할 토큰")
#     reason: str = Field(..., description="블랙리스트 추가 사유")
#     expiry: datetime = Field(..., description="블랙리스트 만료 시간")
#
# class BlacklistedToken(Base):
#     __tablename__ = "blacklisted_tokens"
#
#     token = Column(String, primary_key=True, index=True)
#     reason = Column(String)
#     blacklisted_on = Column(DateTime, default=datetime.utcnow)
#     expiry = Column(DateTime)
#
# async def add_to_blacklist(session: AsyncSession, item: BlackListItem):
#     blacklist_token = BlacklistedToken(
#         token=item.token,
#         reason=item.reason,
#         expiry=item.expiry
#     )
#     session.add(blacklist_token)
#     await session.commit()
#
# async def is_token_blacklisted(session: AsyncSession, token: str) -> bool:
#     result = await session.execute(
#         select(BlacklistedToken).filter(BlacklistedToken.token == token)
#     )
#     return result.scalar() is not None
#
# async def remove_expired_tokens(session: AsyncSession):
#     now = datetime.utcnow()
#     await session.execute(
#         BlacklistedToken.__table__.delete().where(BlacklistedToken.expiry < now)
#     )
#     await session.commit()
#
# async def validate_token(session: AsyncSession, token: str):
#     if await is_token_blacklisted(session, token):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Token has been blacklisted"
#         )
#
# # 주기적으로 실행될 함수 (예: 매일 자정)
# async def cleanup_blacklist(session: AsyncSession):
#     await remove_expired_tokens(session)
