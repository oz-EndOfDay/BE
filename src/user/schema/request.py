from pydantic import BaseModel, Field, constr


class CreateUserRequestBody(BaseModel):
    name: str = Field(..., max_length=35)
    nickname: str = Field(..., max_length=35)
    password: str = Field(..., max_length=100)
    email: str = Field(..., max_length=50)
