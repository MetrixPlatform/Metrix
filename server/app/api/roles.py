from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.permissions import ROLE_CREATE, ROLE_DELETE, ROLE_OPERATE, ROLE_READ, ROLE_UPDATE
from app.db.session import get_db
from app.models import Permission, Role, User
from app.schemas.common import MessageResponse, message_response
from app.schemas.role import AssignPermissionsRequest, PermissionItem, RoleCreateRequest, RoleItem, RoleUpdateRequest
from app.services.roles import RoleService

router = APIRouter(prefix="/api", tags=["roles"])


@router.get("/roles", response_model=list[RoleItem])
def list_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(ROLE_READ)),
) -> list[Role]:
    return RoleService(db).list_roles()


@router.post("/roles", response_model=RoleItem)
def create_role(
    payload: RoleCreateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ROLE_CREATE)),
) -> Role:
    return RoleService(db).create_role(actor.id, payload)


@router.put("/roles/{role_id}", response_model=RoleItem)
def update_role(
    role_id: int,
    payload: RoleUpdateRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ROLE_UPDATE)),
) -> Role:
    return RoleService(db).update_role(actor.id, role_id, payload)


@router.delete("/roles/{role_id}", response_model=MessageResponse)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ROLE_DELETE)),
) -> MessageResponse:
    RoleService(db).delete_role(actor.id, role_id)
    return message_response("permission.roleDeleted", "Role deleted")


@router.get("/permissions", response_model=list[PermissionItem])
def list_permissions(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(ROLE_READ)),
) -> list[Permission]:
    return RoleService(db).list_permissions()


@router.put("/roles/{role_id}/permissions", response_model=RoleItem)
def assign_permissions(
    role_id: int,
    payload: AssignPermissionsRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ROLE_OPERATE)),
) -> Role:
    return RoleService(db).assign_permissions(actor.id, role_id, payload)
