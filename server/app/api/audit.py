from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.permissions import AUDIT_LOG_READ
from app.db.session import get_db
from app.models import User
from app.schemas.audit import AuditLogListResponse
from app.services.audit import AuditService

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("", response_model=AuditLogListResponse)
def list_audit_logs(
    actor_scope: str = "self",
    keyword: str = "",
    action: str = "",
    target_type: str = "",
    source: str = "",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(AUDIT_LOG_READ)),
) -> AuditLogListResponse:
    return AuditService(db).list_logs(
        actor,
        actor_scope,
        keyword,
        action,
        target_type,
        source,
        start_time,
        end_time,
        sort_order,
        page,
        page_size,
    )


@router.get("/export")
def export_audit_logs(
    actor_scope: str = "self",
    keyword: str = "",
    action: str = "",
    target_type: str = "",
    source: str = "",
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    sort_order: str = "descend",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(AUDIT_LOG_READ)),
) -> Response:
    csv_text = AuditService(db).export_csv(
        actor,
        actor_scope,
        keyword,
        action,
        target_type,
        source,
        start_time,
        end_time,
        sort_order,
    )
    return Response(
        content=csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="audit-logs.csv"'},
    )
