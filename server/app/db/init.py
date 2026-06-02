from sqlalchemy.orm import Session

from app.core.permissions import ADMIN_ROLE, PERMISSION_SEEDS, ROUTE_DASHBOARD, USER_ROLE
from app.core.security import hash_password
from app.db.base import Base
from app.models import Permission, Role, User
from app.schemas.install import InstallRequest


def create_tables(engine) -> None:
    Base.metadata.create_all(bind=engine)


def seed_database(db: Session, payload: InstallRequest) -> None:
    permissions_by_code = {}
    for seed in PERMISSION_SEEDS:
        permission = db.query(Permission).filter(Permission.code == seed.code).first()
        if permission is None:
            permission = Permission(
                code=seed.code,
                name=seed.name,
                type=seed.type,
                resource=seed.resource,
                group_name=seed.group_name,
                description=seed.description,
                sort_order=seed.sort_order,
            )
            db.add(permission)
        else:
            permission.name = seed.name
            permission.type = seed.type
            permission.resource = seed.resource
            permission.group_name = seed.group_name
            permission.description = seed.description
            permission.sort_order = seed.sort_order
        permissions_by_code[seed.code] = permission

    admin_role = _ensure_role(db, ADMIN_ROLE, "超级管理员", "拥有全部权限", True)
    user_role = _ensure_role(db, USER_ROLE, "普通用户", "默认基础用户", True)
    admin_role.permissions = list(permissions_by_code.values())
    user_role.permissions = [permissions_by_code[ROUTE_DASHBOARD]]

    admin = db.query(User).filter(User.username == payload.admin_username).first()
    if admin is None:
        admin = User(
            username=payload.admin_username,
            full_name=payload.admin_full_name,
            company=payload.admin_company,
            department=payload.admin_department,
            password_hash=hash_password(payload.admin_password),
            approval_status="approved",
            is_active=True,
            is_builtin=True,
            roles=[admin_role],
        )
        db.add(admin)
    elif admin_role not in admin.roles:
        admin.roles.append(admin_role)

    db.commit()


def _ensure_role(db: Session, code: str, name: str, description: str, is_builtin: bool) -> Role:
    role = db.query(Role).filter(Role.code == code).first()
    if role is None:
        role = Role(code=code, name=name, description=description, is_builtin=is_builtin)
        db.add(role)
    else:
        role.name = name
        role.description = description
        role.is_builtin = is_builtin
    return role
