from pydantic import BaseModel, Field

from app.schemas.user import UserProfile


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    company: str = Field(min_length=1, max_length=120)
    department: str = Field(min_length=1, max_length=120)
    full_name: str = Field(min_length=1, max_length=80)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class ProfileUpdateRequest(BaseModel):
    company: str = Field(min_length=1, max_length=120)
    department: str = Field(min_length=1, max_length=120)
    full_name: str = Field(min_length=1, max_length=80)


class LoginResponse(BaseModel):
    token: str
    user: UserProfile
    permissions: list[str]
