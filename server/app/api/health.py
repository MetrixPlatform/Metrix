from fastapi import APIRouter

from app.core.install import is_installed

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, bool | str]:
    return {"ok": True, "installed": is_installed()}
