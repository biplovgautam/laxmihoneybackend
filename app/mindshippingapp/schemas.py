from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=256)


class SignupResponse(BaseModel):
    success: bool
    message: str
    uid: str
    username: str


class EmailCheckResponse(BaseModel):
    exists: bool


class UsernameCheckResponse(BaseModel):
    exists: bool
