import os

import pytest
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.database.orm import Base

load_dotenv(override=True)

# None 병합 연산자 (??) 사용
TEST_SECRET_KEY = os.getenv("TEST_SECRET_KEY") or "default_test_secret"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or "sqlite+aiosqlite:///test.db"
TEST_REDIS_HOST = os.getenv("TEST_REDIS_HOST") or "localhost"
TEST_REDIS_PORT = os.getenv("TEST_REDIS_PORT") or "6379"


def pytest_configure(config):
    os.environ["SECRET_KEY"] = TEST_SECRET_KEY
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_HOST"] = TEST_REDIS_HOST
    os.environ["REDIS_PORT"] = str(TEST_REDIS_PORT)  # 명시적 문자열 변환


# 나머지 코드 동일


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
