from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.permissions import DEPRECATED_PERMISSION_CODES


class PermissionItem(BaseModel):
    id: int
    code: str
    name: str
    type: str
    resource: str
    group_name: str
    description: str
    sort_order: int

    model_config = {"from_attributes": True}


class RoleItem(BaseModel):
    id: int
    code: str
    name: str
    description: str
    is_builtin: bool
    permissions: list[PermissionItem] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("permissions")
    @classmethod
    def remove_deprecated_permissions(cls, permissions: list[PermissionItem]) -> list[PermissionItem]:
        return [permission for permission in permissions if permission.code not in DEPRECATED_PERMISSION_CODES]


class RoleCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


class RoleUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=500)


class AssignPermissionsRequest(BaseModel):
    permission_ids: list[int]
