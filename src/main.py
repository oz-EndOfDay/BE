from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

# 데이터베이스 관련 모듈
from src.config.database.connection import async_engine

# 라우터 import
from src.user.api.router import router as user_router
from src.user.models import Base


# 비동기 컨텍스트 관리자 사용
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 앱 시작 시 데이터베이스 테이블 생성
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 앱 종료 시 추가 정리 작업 (필요한 경우)


# FastAPI 앱 생성 with lifespan
app = FastAPI(lifespan=lifespan)
# 라우터 포함
app.include_router(user_router)


# 기본 루트 핸들러
@app.get("/")
def root_handler() -> dict[str, str]:
    return {"message": "Hello World"}


# 로컬 실행을 위한 uvicorn 설정
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
