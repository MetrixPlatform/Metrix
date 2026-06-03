from app.core.permissions import ADMIN_ROLE, DEPRECATED_PERMISSION_CODES, expand_permissions
from app.models import User


def get_user_permission_codes(user: User) -> set[str]:
    if any(role.code == ADMIN_ROLE for role in user.roles):
        codes = {permission.code for role in user.roles for permission in role.permissions}
        return active_permission_codes(expand_permissions(codes))
    codes = {permission.code for role in user.roles for permission in role.permissions}
    return active_permission_codes(expand_permissions(codes))


def active_permission_codes(codes: set[str]) -> set[str]:
    return codes - DEPRECATED_PERMISSION_CODES


def has_permission(user: User, permission_code: str) -> bool:
    if any(role.code == ADMIN_ROLE for role in user.roles):
        return True
    return permission_code in get_user_permission_codes(user)
