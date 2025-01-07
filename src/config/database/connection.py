from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings

settings = Settings()

async_engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,  # 연결 풀 크기
    max_overflow=20,  # 최대 추가 연결 수
    pool_timeout=30,  # 연결 대기 시간
    pool_recycle=3600,  # 연결 재사용 시간
)

AsyncSessionFactory = async_sessionmaker(
    bind=async_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()  # db에 커넥션 종료
