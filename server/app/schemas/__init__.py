"""Pydantic schemas."""
from app.schemas.announcement import (
    AnnouncementBatchDeleteRequest,
    AnnouncementFeedItem,
    AnnouncementItem,
    AnnouncementListResponse,
    AnnouncementPayload,
    PublicAnnouncementItem,
)
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse, ProfileUpdateRequest, RegisterRequest
from app.schemas.audit import AuditLogItem, AuditLogListResponse
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
    UserListResponse,
    UserProfile,
    UserUpdateRequest,
)

__all__ = [
    "AssignPermissionsRequest",
    "AssignRolesRequest",
    "AnnouncementBatchDeleteRequest",
    "AnnouncementFeedItem",
    "AnnouncementItem",
    "AnnouncementListResponse",
    "AnnouncementPayload",
    "AuditLogItem",
    "AuditLogListResponse",
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
    "PublicAnnouncementItem",
    "RegisterRequest",
    "RejectUserRequest",
    "ResetPasswordRequest",
    "RoleBrief",
    "RoleCreateRequest",
    "RoleItem",
    "RoleUpdateRequest",
    "UserCreateRequest",
    "UserListItem",
    "UserListResponse",
    "UserProfile",
    "UserUpdateRequest",
]
