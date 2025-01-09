import redis.asyncio as redis
from fastapi import HTTPException, status

from src.config import Settings

settings = Settings()
# Redis 클라이언트 설정
redis_client = redis.Redis(
    host="localhost", port=settings.REDIS_PORT, db=0, decode_responses=True
)


class TokenBlacklist:
    @staticmethod
    async def add_to_blacklist(token: str, expires_in: int) -> None:
        """토큰을 블랙리스트에 추가합니다."""
        await redis_client.setex(f"blacklist:{token}", expires_in, "true")

    @staticmethod
    async def is_blacklisted(token: str) -> bool:
        """토큰이 블랙리스트에 있는지 확인합니다."""
        result = await redis_client.exists(f"blacklist:{token}")
        return bool(result)


async def blacklist_token(token: str, expires_in: int = 3600) -> None:
    """토큰을 블랙리스트에 추가하는 함수입니다."""
    await TokenBlacklist.add_to_blacklist(token, expires_in)


async def check_blacklist(token: str) -> None:
    """토큰이 블랙리스트에 있는지 확인하고, 있다면 예외를 발생시킵니다."""
    if await TokenBlacklist.is_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
        )


# 사용 예시
# from .blacklist import blacklist_token, check_blacklist

# 로그아웃 시
# await blacklist_token(access_token, expires_in=3600)  # 1시간 동안 블랙리스트에 유지

# 토큰 검증 시
# await check_blacklist(access_token)
