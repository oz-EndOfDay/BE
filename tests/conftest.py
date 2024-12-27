import os


def pytest_configure() -> None:
    os.environ["DATABASE_URL"] = (
        "postgresql+asyncpg://admin:admin_pw@localhost:9999/endofday_test"
    )
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["REDIS_PORT"] = "6379"
