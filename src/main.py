import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src import user
from src.config.database.connection import engine
from src.user.api.router import router as user_router
from src.user.models import Base

# 비동기 컨텍스트 관리자 사용
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 앱 시작 시 데이터베이스 테이블 생성
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 앱 종료 시 추가 정리 작업 (필요한 경우)

app = FastAPI(lifespan=lifespan)


# async def create_tables() -> None:
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)
#
#
# asyncio.run(create_tables())
app.include_router(user_router)


@app.get("/")
def root_handler() -> dict[str, str]:
    return {"message": "Hello World"}


# GitHub Actions에서 실행을 위한 추가 코드
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
