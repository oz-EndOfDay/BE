import os

from dotenv import load_dotenv

load_dotenv(override=True)

TEST_SECRET_KEY = os.getenv("TEST_SECRET_KEY", "default_test_secret_key")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "default_test_database_url")
TEST_REDIS_HOST = os.getenv("TEST_REDIS_HOST", "default_test_redis_host")
TEST_REDIS_PORT = os.getenv("TEST_REDIS_PORT", "default_test_redis_port")


def pytest_configure() -> None:
    os.environ["SECRET_KEY"] = TEST_SECRET_KEY
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_HOST"] = TEST_REDIS_HOST
    os.environ["REDIS_PORT"] = TEST_REDIS_PORT


import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.database.orm import Base  # 데이터베이스 Base 모델


@pytest.fixture(scope="function")
async def async_session():
    # 테스트용 임시 데이터베이스 엔진 생성
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)

    # 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 세션 생성
    AsyncTestingSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

    # 테스트 후 데이터베이스 삭제
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
