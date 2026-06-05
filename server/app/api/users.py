from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permission
from app.core.permissions import USER_CREATE, USER_DELETE, USER_OPERATE, USER_READ, USER_UPDATE
from app.db.session import get_db
from app.models import Role, User
from app.schemas.common import MessageResponse, message_response
from app.schemas.user import (
    AssignRolesRequest,
    RejectUserRequest,
    ResetPasswordRequest,
    RoleBrief,
    UserCreateRequest,
    UserListItem,
    UserListResponse,
    UserUpdateRequest,
)
from app.services.users import UserService

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    keyword: str = "",
    approval_status: str = "",
    is_active: bool | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USER_READ)),
) -> UserListResponse:
    return UserService(db).list_users(
        keyword,
        approval_status,
        is_active,
        start_time,
        end_time,
        sort_order,
        page,
        page_size,
    )


@router.get("/role-options", response_model=list[RoleBrief])
def list_role_options(
    db: Session = Depends(get_db),
    _: User = Depends(require_any_permission(USER_CREATE, USER_OPERATE)),
) -> list[Role]:
    return UserService(db).list_role_options()


@router.get("/{user_id}", response_model=UserListItem)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USER_READ)),
) -> User:
    return UserService(db).get_user(user_id)


@router.post("", response_model=UserListItem)
def create_user(
    payload: UserCreateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_CREATE)),
) -> User:
    return UserService(db).create_user(actor, payload)


@router.put("/{user_id}", response_model=UserListItem)
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_UPDATE)),
) -> User:
    return UserService(db).update_user(actor, user_id, payload)


@router.delete("/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_DELETE)),
) -> MessageResponse:
    UserService(db).delete_user(actor, user_id)
    return message_response("user.deleted", "User deleted")


@router.post("/{user_id}/enable", response_model=UserListItem)
def enable_user(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> User:
    return UserService(db).enable_user(actor, user_id)


@router.post("/{user_id}/disable", response_model=UserListItem)
def disable_user(
    user_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> User:
    return UserService(db).disable_user(actor, user_id)


@router.post("/{user_id}/reset-password", response_model=MessageResponse)
def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> MessageResponse:
    UserService(db).reset_password(actor, user_id, payload)
    return message_response("user.passwordReset", "Password reset")


@router.put("/{user_id}/roles", response_model=UserListItem)
def assign_roles(
    user_id: int,
    payload: AssignRolesRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> User:
    return UserService(db).assign_roles(actor, user_id, payload)


@router.post("/{user_id}/approve", response_model=UserListItem)
def approve_user(
    user_id: int,
    payload: AssignRolesRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> User:
    return UserService(db).approve_user(actor, user_id, payload.role_ids)


@router.post("/{user_id}/reject", response_model=UserListItem)
def reject_user(
    user_id: int,
    payload: RejectUserRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> User:
    return UserService(db).reject_user(actor, user_id, payload)
