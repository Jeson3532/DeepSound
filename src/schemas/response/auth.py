from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserRegisterResponse(BaseModel):
    id: int = Field(...)
    username: str = Field(..., min_length=3, max_length=16)
    email: EmailStr = Field(...)

    model_config = ConfigDict(from_attributes=True)


class UserRegisterResponseSuccess(UserRegisterResponse):
    session_id: int = Field()
