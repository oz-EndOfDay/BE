from redis import Redis

from config import settings

redis_client = Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=0,
    encoding="utf-8",
    decode_responses=True,
)
