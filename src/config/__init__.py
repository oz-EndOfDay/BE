from enum import StrEnum
from typing import Any, Dict, TypeVar

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()
T = TypeVar("T", bound="Settings")


class ServerEnv(StrEnum):
    LOCAL = "local"  # 내 로컬 환경
    DEV = "dev"  # 개발 서버
    PROD = "prod"  # 프로덕션 서버


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_HOST: str
    REDIS_PORT: int
    SECRET_KEY: str
    EMAIL_PASSWORD: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @classmethod
    def get_config(cls: type[T]) -> Dict[str, Any]:
        settings = cls()
        result: Dict[str, Any] = settings.model_dump()
        return result
