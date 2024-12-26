import os
from enum import StrEnum

from pydantic_settings import BaseSettings


class ServerEnv(StrEnum):
    LOCAL = "local"  # 내 로컬 환경
    DEV = "dev"  # 개발 서버
    PROD = "prod"  # 프로덕션 서버


class Settings(BaseSettings):
    database_url: str
    redis_host: str
    redis_port: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
