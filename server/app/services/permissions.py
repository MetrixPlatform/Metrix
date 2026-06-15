from sqlalchemy.orm import object_session

from app.core.permissions import ADMIN_ROLE, DEPRECATED_PERMISSION_CODES, expand_permissions
from app.models import Permission, User


def get_user_permission_codes(user: User) -> set[str]:
    codes = _all_permission_codes(user) if _is_admin(user) else {permission.code for role in user.roles for permission in role.permissions}
    return active_permission_codes(expand_permissions(codes))


def active_permission_codes(codes: set[str]) -> set[str]:
    return codes - DEPRECATED_PERMISSION_CODES


def has_permission(user: User, permission_code: str) -> bool:
    if _is_admin(user):
        return True
    return permission_code in get_user_permission_codes(user)


def _is_admin(user: User) -> bool:
    return any(role.code == ADMIN_ROLE for role in user.roles)


def _all_permission_codes(user: User) -> set[str]:
    session = object_session(user)
    if session is None:
        return {permission.code for role in user.roles for permission in role.permissions}
    return {code for (code,) in session.query(Permission.code).all()}
