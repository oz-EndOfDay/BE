import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi_pagination import add_pagination

# 데이터베이스 관련 모듈
from src.config.database.connection import async_engine
from src.config.database.connection_async import async_engine
from src.config.database.orm import Base
from src.diary.api.router import router as diary_router
from src.ex_diary.api.router import router as ex_diary_router
from src.friend.api.router import router as friend_router
from src.notification.api.router import router as notification_router
from src.notification.service.websocket import router as w_router

# 라우터 import
from src.user.api.router import router as user_router
from src.user.models import Base
from src.user.service.tasks import periodic_cleanup
from src.websocket.api.router import router as websocket_router

logger = logging.getLogger(__name__)


# 비동기 컨텍스트 관리자 사용
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 앱 시작 시 데이터베이스 테이블 생성
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 유저 클린업 관리
    logger.info("main.py -> startup_event")
    asyncio.create_task(periodic_cleanup())
    yield
    # 앱 종료 시 추가 정리 작업 (필요한 경우)


# FastAPI 앱 생성 with lifespan
app = FastAPI(lifespan=lifespan)
# 라우터 포함

origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "https://endofday.store",
    "https://www.endofday.store",
    "https://fe-three-omega.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)


app.include_router(user_router)
app.include_router(friend_router)
app.include_router(diary_router)
app.include_router(ex_diary_router)
app.include_router(notification_router)
app.include_router(websocket_router)
app.include_router(w_router)
add_pagination(app)


# 기본 루트 핸들러
@app.get("/")
async def root() -> dict[str, str]:
    print("main.py -> root")
    return {"message": "Hello World"}


# 로컬 실행을 위한 uvicorn 설정
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
