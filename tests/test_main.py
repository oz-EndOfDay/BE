from fastapi.testclient import TestClient

from src.config import Settings
from src.config.database.connection_async import async_engine
from src.main import app

client = TestClient(app)


def test_read_main() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_settings() -> None:
    settings = Settings()
    assert settings.DATABASE_URL is not None
