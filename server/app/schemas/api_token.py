from datetime import datetime

from pydantic import BaseModel, Field


class ApiTokenCreateRequest(BaseModel):
    name: str = Field(max_length=80)
    expires_at: datetime | None = None


class ApiTokenItem(BaseModel):
    id: int
    name: str
    token_prefix: str
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiTokenCreateResponse(ApiTokenItem):
    token: str
