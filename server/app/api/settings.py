from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.permissions import SETTING_OPERATE, SETTING_READ, SETTING_UPDATE
from app.db.session import get_db
from app.models import User
from app.schemas.settings import PublicSettings, SystemSettings, SystemSettingsUpdate
from app.services.settings import SettingService

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/public", response_model=PublicSettings)
def public_settings(db: Session = Depends(get_db)) -> PublicSettings:
    return SettingService(db).public_settings()


@router.get("", response_model=SystemSettings)
def get_system_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(SETTING_READ)),
) -> SystemSettings:
    return SettingService(db).get_settings()


@router.put("", response_model=SystemSettings)
def update_system_settings(
    payload: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SETTING_UPDATE)),
) -> SystemSettings:
    return SettingService(db).update_settings(actor, payload)


@router.post("/backup")
def backup_data(
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(SETTING_OPERATE)),
) -> Response:
    backup = SettingService(db).backup_data(actor)
    filename = f"metrix-backup-{datetime.now().strftime('%Y%m%d%H%M%S')}.zip"
    return Response(
        content=backup,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
