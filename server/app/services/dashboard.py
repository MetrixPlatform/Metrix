from sqlalchemy.orm import Session

from app.repositories.roles import RoleRepository
from app.repositories.users import UserRepository
from app.schemas.dashboard import DashboardSummary


def get_dashboard_summary(db: Session) -> DashboardSummary:
    users = UserRepository(db)
    roles = RoleRepository(db)
    return DashboardSummary(
        user_count=users.count(),
        pending_user_count=users.count("pending"),
        role_count=roles.count(),
        permission_count=roles.permission_count(),
    )
