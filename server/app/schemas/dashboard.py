from pydantic import BaseModel


class DashboardSummary(BaseModel):
    user_count: int
    pending_user_count: int
    role_count: int
    permission_count: int
