from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = "postgresql+asyncpg://admin:admin_pw@localhost:9999/endofday"


async_engine = create_async_engine(DATABASE_URL)
AsyncSessionFactory = async_sessionmaker(
    bind=async_engine, autocommit=False, autoflush=False, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSessionFactory()
    try:
        yield session
    finally:
        await session.close()  # db에 커넥션 종료
