import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from celery import Celery
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from src.config import Settings

# 데이터베이스 관련 모듈
from src.config.database.connection import async_engine
from src.diary.api.router import router as diary_router
from src.ex_diary.api.router import router as ex_diary_router
from src.friend.api.router import router as friend_router
from src.notification.api.router import router as notification_router
from src.notification.service.websocket import router as w_router

# 라우터 import
from src.user.api.router import router as user_router
from src.user.models import Base
from src.websocket.api.router import router as websocket_router

logger = logging.getLogger(__name__)

settings = Settings()

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT

# Celery 앱 초기화
celery_app = Celery(
    "tasks",
    broker="redis://{REDIS_HOST}:{REDIS_PORT}}/0",
    backend="redis://{REDIS_HOST}:{REDIS_PORT}}/0",
)
celery_app.config_from_object("src.config.celery_config")  # Celery 설정 로드


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 앱 시작 시 데이터베이스 테이블 생성
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    # 앱 종료 시 추가 정리 작업 (필요한 경우)


# FastAPI 앱 생성 with lifespan
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "https://endofday.store",
    "https://api.endofday.store",
    "https://www.endofday.store",
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


@app.get("/")
async def root() -> dict[str, str]:
    print("main.py -> root")
    return {"message": "Hello World"}


# 루트 로거 설정
# logging.basicConfig(
#     level=logging.INFO,  # INFO 이상의 모든 로그 기록
#     format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.FileHandler("/home/ubuntu/log/error.log"),  # ERROR 로그 파일
#         logging.FileHandler("/home/ubuntu/log/info.log"),  # INFO 로그 파일
#         logging.StreamHandler(),
#     ],
# )


@app.get("/error")
def create_error() -> dict[str, str]:
    try:
        # 의도적인 오류 발생
        1 / 0
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
    return {"message": "Error test"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
