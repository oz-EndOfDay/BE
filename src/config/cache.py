from redis import Redis

from src.config import Settings

settings = Settings()

redis_client = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=0,
    encoding="utf-8",
    decode_responses=True,
)
