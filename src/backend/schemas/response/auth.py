from pydantic import BaseModel, Field, EmailStr


class UserRegisterResponse(BaseModel):
    id: int = Field(...)
    username: str = Field(..., min_length=3, max_length=16)
    email: EmailStr = Field(...)
