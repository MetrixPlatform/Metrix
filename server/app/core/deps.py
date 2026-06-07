from collections.abc import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import forbidden, unauthorized
from app.core.permissions import API_TOKEN_READ
from app.core.security import API_TOKEN_PREFIX, decode_access_token, hash_api_token
from app.core.time import utc_now
from app.db.session import get_db
from app.models import ApiToken, User
from app.repositories.api_tokens import ApiTokenRepository
from app.repositories.users import UserRepository
from app.services.permissions import has_permission
from app.services.settings import SettingService

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> User:
    if credentials is None:
        raise unauthorized("error.authRequired", "Authentication required")
    token = credentials.credentials
    subject = decode_access_token(token)
    if subject is None:
        return _get_api_token_user(db, token)
    user = UserRepository(db).get(int(subject))
    return _guard_user_available(user)


def require_api_feature_enabled(db: Session = Depends(get_db)) -> None:
    if not SettingService(db).get_settings().api_enabled:
        raise forbidden("error.apiDisabled", "API feature is disabled")


def _get_api_token_user(db: Session, plain_token: str) -> User:
    if not plain_token.startswith(API_TOKEN_PREFIX):
        raise unauthorized("error.authExpired", "Session expired")
    if not SettingService(db).get_settings().api_enabled:
        raise forbidden("error.apiDisabled", "API feature is disabled")
    api_token = ApiTokenRepository(db).get_by_hash(hash_api_token(plain_token))
    if not _is_api_token_available(api_token):
        raise unauthorized("error.authExpired", "Session expired")
    user = _guard_user_available(api_token.user)
    if not has_permission(user, API_TOKEN_READ):
        raise forbidden()
    api_token.last_used_at = utc_now()
    db.commit()
    return user


def _guard_user_available(user: User | None) -> User:
    if not user or not user.is_active or user.approval_status != "approved":
        raise unauthorized("error.accountUnavailable", "Account unavailable")
    return user


def _is_api_token_available(api_token: ApiToken | None) -> bool:
    if not api_token or not api_token.is_active:
        return False
    if api_token.expires_at is None:
        return True
    now = utc_now()
    comparable_now = now.replace(tzinfo=None) if api_token.expires_at.tzinfo is None else now
    return api_token.expires_at > comparable_now


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
