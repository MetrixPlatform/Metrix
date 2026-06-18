from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.core.permissions import DASHBOARD_READ
from app.db.session import get_db
from app.models import User
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard import get_dashboard_summary

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(DASHBOARD_READ)),
) -> DashboardSummary:
    return get_dashboard_summary(db)
