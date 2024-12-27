from redis import Redis

from src.config import Settings

redis_client = Redis(
    host=Settings.redis_host,
    port=Settings.redis_port,
    db=0,
    encoding="utf-8",
    decode_responses=True,
)
