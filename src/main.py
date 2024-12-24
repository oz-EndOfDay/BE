from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root_handler():
    return {"message": "Hello World"}