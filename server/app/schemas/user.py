from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import normalize_email, normalize_phone


class RoleBrief(BaseModel):
    id: int
    code: str
    name: str

    model_config = {"from_attributes": True}


class UserProfile(BaseModel):
    id: int
    username: str
    full_name: str
    phone: str
    email: str
    company: str
    department: str
    approval_status: str
    is_active: bool
    is_builtin: bool
    roles: list[RoleBrief] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UserListItem(UserProfile):
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    items: list[UserListItem]
    total: int
    page: int
    page_size: int


class UserCreateRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=1, max_length=20)
    email: str = Field(min_length=1, max_length=254)
    company: str = Field(default="", max_length=120)
    department: str = Field(default="", max_length=120)
    role_ids: list[int] = Field(default_factory=list)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)


class UserUpdateRequest(BaseModel):
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


class ResetPasswordRequest(BaseModel):
    password: str = Field(min_length=6, max_length=128)


class RejectUserRequest(BaseModel):
    reason: str = Field(default="", max_length=500)


class AssignRolesRequest(BaseModel):
    role_ids: list[int]
