"""Pydantic schemas."""
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, ProfileUpdateRequest, RegisterRequest
from app.schemas.common import MessageResponse
from app.schemas.dashboard import DashboardSummary
from app.schemas.install import InstallRequest, InstallStatusResponse, MysqlInstallConfig
from app.schemas.role import AssignPermissionsRequest, PermissionItem, RoleCreateRequest, RoleItem, RoleUpdateRequest
from app.schemas.user import (
    AssignRolesRequest,
    RejectUserRequest,
    ResetPasswordRequest,
    RoleBrief,
    UserCreateRequest,
    UserListItem,
    UserProfile,
    UserUpdateRequest,
)

__all__ = [
    "AssignPermissionsRequest",
    "AssignRolesRequest",
    "ChangePasswordRequest",
    "DashboardSummary",
    "InstallRequest",
    "InstallStatusResponse",
    "LoginRequest",
    "LoginResponse",
    "MessageResponse",
    "MysqlInstallConfig",
    "PermissionItem",
    "ProfileUpdateRequest",
    "RegisterRequest",
    "RejectUserRequest",
    "ResetPasswordRequest",
    "RoleBrief",
    "RoleCreateRequest",
    "RoleItem",
    "RoleUpdateRequest",
    "UserCreateRequest",
    "UserListItem",
    "UserProfile",
    "UserUpdateRequest",
]
