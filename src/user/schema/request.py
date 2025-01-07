from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


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
    modified_at: datetime = Field(...)
    is_active: Optional[bool] = Field(
        None,
    )