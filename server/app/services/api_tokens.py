from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.core.security import create_api_token, hash_api_token
from app.core.time import utc_now
from app.models import ApiToken, User
from app.repositories.api_tokens import ApiTokenRepository
from app.schemas.api_token import ApiTokenCreateRequest, ApiTokenCreateResponse, ApiTokenItem
from app.services.audit import record_audit
from app.services.settings import SettingService


class ApiTokenService:
    def __init__(self, db: Session):
        self.db = db
        self.tokens = ApiTokenRepository(db)

    def list_tokens(self, user: User) -> list[ApiToken]:
        return self.tokens.list_for_user(user.id)

    def create_token(self, user: User, payload: ApiTokenCreateRequest) -> ApiTokenCreateResponse:
        name = payload.name.strip()
        if not name:
            raise bad_request("error.apiTokenNameRequired", "API token name is required")
        expires_at = self._validate_expiry(payload.expires_at)
        plain_token = self._new_unique_token()
        api_token = self.tokens.create(
            ApiToken(
                user_id=user.id,
                name=name,
                token_hash=hash_api_token(plain_token),
                token_prefix=plain_token[:12],
                token_value=plain_token,
                expires_at=expires_at,
            )
        )
        record_audit(self.db, user.id, "api_token.create", "api_token", str(api_token.id), api_token.name)
        self.db.commit()
        data = ApiTokenItem.model_validate(api_token).model_dump()
        return ApiTokenCreateResponse(**data, token=plain_token)

    def delete_token(self, user: User, token_id: int) -> None:
        api_token = self.tokens.get_for_user(token_id, user.id)
        if not api_token:
            raise not_found("error.apiTokenNotFound", "API token not found")
        name = api_token.name
        record_audit(self.db, user.id, "api_token.delete", "api_token", str(api_token.id), name)
        self.tokens.delete(api_token)
        self.db.commit()

    def get_token_secret(self, user: User, token_id: int) -> str:
        if not SettingService(self.db).get_settings().api_token_reveal_enabled:
            raise forbidden("error.apiTokenRevealDisabled", "API token reveal is disabled")
        api_token = self.tokens.get_for_user(token_id, user.id)
        if not api_token:
            raise not_found("error.apiTokenNotFound", "API token not found")
        if not api_token.token_value:
            raise not_found("error.apiTokenSecretUnavailable", "API token secret is unavailable")
        return api_token.token_value

    def _new_unique_token(self) -> str:
        for _ in range(5):
            token = create_api_token()
            if not self.tokens.get_by_hash(hash_api_token(token)):
                return token
        raise bad_request("error.apiTokenCreateFailed", "Failed to create API token")

    def _validate_expiry(self, expires_at: datetime | None) -> datetime | None:
        if expires_at is None:
            return None
        now = utc_now()
        comparable_now = now.replace(tzinfo=None) if expires_at.tzinfo is None else now
        if expires_at <= comparable_now:
            raise bad_request("error.apiTokenExpiredAtInvalid", "Expiration time must be in the future")
        return expires_at
