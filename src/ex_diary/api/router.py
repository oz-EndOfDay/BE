from fastapi import APIRouter

from src.config import Settings

router = APIRouter(prefix="/ex_diary", tags=["Exchange Diary"])
settings = Settings()