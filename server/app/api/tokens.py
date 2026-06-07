from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_api_feature_enabled, require_permission, require_web_session
from app.core.permissions import API_TOKEN_CREATE, API_TOKEN_DELETE, API_TOKEN_READ
from app.db.session import get_db
from app.models import User
from app.schemas.api_token import ApiTokenCreateRequest, ApiTokenCreateResponse, ApiTokenItem, ApiTokenSecretResponse
from app.schemas.common import MessageResponse, message_response
from app.services.api_tokens import ApiTokenService

router = APIRouter(
    prefix="/api/tokens",
    tags=["api-tokens"],
    dependencies=[Depends(require_api_feature_enabled), Depends(require_web_session)],
)


@router.get("", response_model=list[ApiTokenItem])
def list_tokens(
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(API_TOKEN_READ)),
) -> list[ApiTokenItem]:
    return [ApiTokenItem.model_validate(token) for token in ApiTokenService(db).list_tokens(user)]


@router.post("", response_model=ApiTokenCreateResponse)
def create_token(
    payload: ApiTokenCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(API_TOKEN_CREATE)),
) -> ApiTokenCreateResponse:
    return ApiTokenService(db).create_token(user, payload)


@router.get("/{token_id}/secret", response_model=ApiTokenSecretResponse)
def get_token_secret(
    token_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(API_TOKEN_READ)),
) -> ApiTokenSecretResponse:
    return ApiTokenSecretResponse(token=ApiTokenService(db).get_token_secret(user, token_id))


@router.delete("/{token_id}", response_model=MessageResponse)
def delete_token(
    token_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(API_TOKEN_DELETE)),
) -> MessageResponse:
    ApiTokenService(db).delete_token(user, token_id)
    return message_response("token.deleted", "API token deleted")
