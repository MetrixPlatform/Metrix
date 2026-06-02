from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.permissions import USER_OPERATE, USER_READ
from app.db.session import get_db
from app.models import User
from app.schemas.user import AssignRolesRequest, RejectUserRequest, UserListItem
from app.services.users import UserService

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("/users", response_model=list[UserListItem])
def pending_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(USER_READ)),
) -> list[User]:
    return UserService(db).list_pending_users()


@router.post("/users/{user_id}/approve", response_model=UserListItem)
def approve_user(
    user_id: int,
    payload: AssignRolesRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> User:
    return UserService(db).approve_user(actor, user_id, payload.role_ids)


@router.post("/users/{user_id}/reject", response_model=UserListItem)
def reject_user(
    user_id: int,
    payload: RejectUserRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(USER_OPERATE)),
) -> User:
    return UserService(db).reject_user(actor, user_id, payload)
