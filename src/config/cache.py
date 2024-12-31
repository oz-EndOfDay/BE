from redis import Redis

from src.config import Settings

settings = Settings()

redis_client = Redis(
    host=Settings.REDIS_HOST,
    port=Settings.REDIS_PORT,
    db=0,
    encoding="utf-8",
    decode_responses=True,
)
