from pydantic import BaseModel, Field, field_validator

from app.schemas.common import normalize_email, normalize_phone
from app.schemas.user import UserProfile


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=80)
    phone: str = Field(default="", max_length=20)
    email: str = Field(default="", max_length=254)
    company: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value) if value.strip() else ""

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value) if value.strip() else ""


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=1, max_length=20)
    email: str = Field(min_length=1, max_length=254)
    company: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class LoginResponse(BaseModel):
    token: str
    user: UserProfile
    permissions: list[str]
