from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class DemoItemPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=1000)
    is_active: bool = True

    @field_validator("name", "category", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class DemoItemItem(DemoItemPayload):
    id: int
    created_by: int | None
    created_by_username: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DemoItemListResponse(BaseModel):
    items: list[DemoItemItem]
    total: int
    page: int
    page_size: int
