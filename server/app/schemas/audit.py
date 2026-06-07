from datetime import datetime
import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AuditLogItem(BaseModel):
    id: int
    actor_user_id: int | None
    actor_username: str = ""
    action: str
    target_type: str
    target_id: str
    detail: str
    detail_data: dict[str, Any] = Field(default_factory=dict)
    source: str = "web"
    api_token_prefix: str = ""
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("detail_data", mode="before")
    @classmethod
    def parse_detail_data(cls, value: object) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if not isinstance(value, str) or not value.strip():
            return {}
        try:
            parsed = json.loads(value)
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int
