from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import forbidden, unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.repositories.users import UserRepository
from app.services.permissions import has_permission

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if credentials is None:
        raise unauthorized("error.authRequired", "Authentication required")
    subject = decode_access_token(credentials.credentials)
    if subject is None:
        raise unauthorized("error.authExpired", "Session expired")
    user = UserRepository(db).get(int(subject))
    if not user or not user.is_active or user.approval_status != "approved":
        raise unauthorized("error.accountUnavailable", "Account unavailable")
    return user


def require_permission(permission_code: str) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not has_permission(user, permission_code):
            raise forbidden()
        return user

    return dependency


def require_any_permission(*permission_codes: str) -> Callable[[User], User]:
    def dependency(user: User = Depends(get_current_user)) -> User:
        if not any(has_permission(user, permission_code) for permission_code in permission_codes):
            raise forbidden()
        return user

    return dependency
