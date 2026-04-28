from pydantic import BaseModel, Field, EmailStr


class UserLogin(BaseModel):
    username: str = Field(...)
    password: str = Field(...)


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=16)
    email: EmailStr = Field(...)
    password: str = Field(..., min_length=8, max_length=64)
    repeat_password: str = Field(..., min_length=8, max_length=64)


