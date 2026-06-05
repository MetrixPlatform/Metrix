from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

ANNOUNCEMENT_TARGET_TYPES = {"all", "authenticated", "permission", "company", "company_department", "user"}


class AnnouncementPayload(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=2000)
    target_type: str = "all"
    target_value: str = Field(default="", max_length=1000)
    show_popup: bool = False
    show_ticker: bool = True
    show_sidebar: bool = True
    is_active: bool = True

    @field_validator("target_type")
    @classmethod
    def validate_target_type(cls, value: str) -> str:
        if value not in ANNOUNCEMENT_TARGET_TYPES:
            raise PydanticCustomError("validation.announcementTargetType", "Invalid announcement target type")
        return value

    @model_validator(mode="after")
    def validate_payload(self):
        if self.target_type not in {"all", "authenticated"} and not self.target_value.strip():
            raise PydanticCustomError("validation.announcementTargetRequired", "Announcement target is required")
        if not any([self.show_popup, self.show_ticker, self.show_sidebar]):
            raise PydanticCustomError("validation.displayModeRequired", "Select at least one display mode")
        if self.target_type in {"all", "authenticated"}:
            self.target_value = ""
        return self


class AnnouncementBatchDeleteRequest(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=200)


class AnnouncementItem(AnnouncementPayload):
    id: int
    created_by: int | None
    created_by_username: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnnouncementListResponse(BaseModel):
    items: list[AnnouncementItem]
    total: int
    page: int
    page_size: int


class AnnouncementFeedItem(AnnouncementItem):
    is_read: bool = False
    read_at: datetime | None = None


class PublicAnnouncementItem(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}
