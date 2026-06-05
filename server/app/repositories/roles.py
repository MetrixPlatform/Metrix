from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.permissions import DEPRECATED_PERMISSION_CODES
from app.models import Permission, Role


class RoleRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, role_id: int) -> Role | None:
        return self.db.get(Role, role_id)

    def get_by_code(self, code: str) -> Role | None:
        return self.db.query(Role).filter(Role.code == code).first()

    def by_ids(self, role_ids: list[int]) -> list[Role]:
        if not role_ids:
            return []
        return self.db.query(Role).filter(Role.id.in_(role_ids)).all()

    def list(self) -> list[Role]:
        return self.db.query(Role).order_by(Role.is_builtin.desc(), Role.id.asc()).all()

    def create(self, role: Role) -> Role:
        self.db.add(role)
        self.db.flush()
        return role

    def delete(self, role: Role) -> None:
        self.db.delete(role)
        self.db.flush()

    def permissions(self) -> list[Permission]:
        return self._active_permissions_query().order_by(Permission.sort_order.asc(), Permission.id.asc()).all()

    def permissions_by_ids(self, permission_ids: list[int]) -> list[Permission]:
        if not permission_ids:
            return []
        return self._active_permissions_query().filter(Permission.id.in_(permission_ids)).all()

    def count(self) -> int:
        return self.db.query(Role).count()

    def permission_count(self) -> int:
        return self._active_permissions_query().count()

    def _active_permissions_query(self):
        query = self.db.query(Permission)
        if DEPRECATED_PERMISSION_CODES:
            query = query.filter(Permission.code.not_in(DEPRECATED_PERMISSION_CODES))
        return query
