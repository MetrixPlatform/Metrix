from datetime import datetime

from pydantic import BaseModel


class AuditLogItem(BaseModel):
    id: int
    actor_user_id: int | None
    actor_username: str = ""
    action: str
    target_type: str
    target_id: str
    detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int
