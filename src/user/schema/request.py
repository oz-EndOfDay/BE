from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateRequestBody(BaseModel):
    name: str = Field(..., max_length=35)
    nickname: str = Field(..., max_length=35)
    email: str = Field(..., max_length=50)
    password: str


class UpdateRequestBody(BaseModel):
    name: Optional[str] = Field(None, max_length=35)
    nickname: Optional[str] = Field(None, max_length=35)
    password: Optional[str] = Field(
        None,
    )
    introduce: Optional[str] = Field(
        None,
    )
    img_url: Optional[str] = Field(
        None,
    )

class UserEmailRequest(BaseModel):
    email: str = Field(..., max_length=50)

