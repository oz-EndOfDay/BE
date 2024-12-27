from pydantic import BaseModel, Field


class CreateRequestBody(BaseModel):
    name: str = Field(..., max_length=35)
    nickname: str = Field(..., max_length=35)
    email: str = Field(..., max_length=50)
    password: str
