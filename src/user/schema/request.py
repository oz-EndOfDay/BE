from datetime import datetime

from pydantic import BaseModel, Field


class CreateRequestBody(BaseModel):
    name: str = Field(..., max_length=35)
    nickname: str = Field(..., max_length=35)
    email: str = Field(..., max_length=50)
    password: str


class UpdateRequestBody(BaseModel):
    name: str = Field(..., max_length=35)
    nickname: str = Field(..., max_length=35)
    password: str = Field(..., max_length=50)
    introduce: str = Field(...)
    img_url: str = Field(...)
    modified_at: datetime = Field(...)
