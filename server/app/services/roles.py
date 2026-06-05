from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.core.permissions import ADMIN_ROLE
from app.models import Permission, Role
from app.repositories.roles import RoleRepository
from app.schemas.role import AssignPermissionsRequest, RoleCreateRequest, RoleUpdateRequest
from app.services.audit import record_audit


class RoleService:
    def __init__(self, db: Session):
        self.db = db
        self.roles = RoleRepository(db)

    def list_roles(self) -> list[Role]:
        return self.roles.list()

    def list_permissions(self) -> list[Permission]:
        return self.roles.permissions()

    def get_role(self, role_id: int) -> Role:
        role = self.roles.get(role_id)
        if not role:
            raise not_found("error.roleNotFound", "Role not found")
        return role

    def create_role(self, actor_id: int, payload: RoleCreateRequest) -> Role:
        if self.roles.get_by_code(payload.code):
            raise bad_request("error.roleCodeExists", "Role code already exists")
        role = self.roles.create(Role(code=payload.code, name=payload.name, description=payload.description))
        record_audit(self.db, actor_id, "role.create", "role", str(role.id), role.code)
        self.db.commit()
        return role

    def update_role(self, actor_id: int, role_id: int, payload: RoleUpdateRequest) -> Role:
        role = self.get_role(role_id)
        role.name = payload.name
        role.description = payload.description
        record_audit(self.db, actor_id, "role.update", "role", str(role.id), role.code)
        self.db.commit()
        return role

    def delete_role(self, actor_id: int, role_id: int) -> None:
        role = self.get_role(role_id)
        if role.is_builtin:
            raise forbidden("error.builtinRoleCannotDelete", "Built-in roles cannot be deleted")
        record_audit(self.db, actor_id, "role.delete", "role", str(role.id), role.code)
        self.roles.delete(role)
        self.db.commit()

    def assign_permissions(self, actor_id: int, role_id: int, payload: AssignPermissionsRequest) -> Role:
        role = self.get_role(role_id)
        if role.code == ADMIN_ROLE:
            role.permissions = self.roles.permissions()
        else:
            role.permissions = self.roles.permissions_by_ids(payload.permission_ids)
        record_audit(self.db, actor_id, "role.assign_permissions", "role", str(role.id), role.code)
        self.db.commit()
        return role
