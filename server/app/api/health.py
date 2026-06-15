from fastapi import APIRouter, Depends, Request

from app.core.deps import require_api_feature_enabled, require_permission
from app.core.install import is_installed
from app.core.network import list_base_urls
from app.core.permissions import API_DOCS_READ
from app.models import User

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, bool | str]:
    return {"ok": True, "installed": is_installed()}


@router.get("/base-urls")
def base_urls(
    request: Request,
    _: None = Depends(require_api_feature_enabled),
    __: User = Depends(require_permission(API_DOCS_READ)),
) -> dict[str, list[str]]:
    return {"base_urls": list_base_urls(request)}
