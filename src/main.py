from fastapi import FastAPI

from src.websockets.router import router

app = FastAPI()

app.include_router(router)


@app.get("/")
def root_handler() -> dict[str, str]:
    return {"message": "Hello World"}


# GitHub Actions에서 실행을 위한 추가 코드
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8000)
