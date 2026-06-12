import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

STORAGE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
ENTRY_NAME_INVALID_CHARS = ("/", "\\")


def normalize_base_path_value(value: str) -> str:
    cleaned = value.strip().replace("\\", "/")
    segments = [segment for segment in cleaned.split("/") if segment not in ("", ".")]
    if any(segment == ".." for segment in segments):
        raise PydanticCustomError("validation.invalidFormat", "Invalid base path")
    return "/" + "/".join(segments) if segments else "/"


class StorageConnectionPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    storage_id: str = Field(default="", max_length=64)
    protocol: Literal["ftp", "sftp"]
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(default="", max_length=255)
    base_path: str = Field(default="/", max_length=500)
    is_shared: bool = False
    is_active: bool = True

    @field_validator("name", "host", "username")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("storage_id")
    @classmethod
    def validate_storage_id(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned and not STORAGE_ID_RE.fullmatch(cleaned):
            raise PydanticCustomError("validation.storageId", "Storage ID must be 3-64 letters, digits, - or _")
        return cleaned

    @field_validator("base_path")
    @classmethod
    def normalize_base_path(cls, value: str) -> str:
        return normalize_base_path_value(value)


class StorageTestRequest(BaseModel):
    id: int | None = None
    protocol: Literal["ftp", "sftp"]
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(default="", max_length=255)
    base_path: str = Field(default="/", max_length=500)

    @field_validator("host", "username")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("base_path")
    @classmethod
    def normalize_base_path(cls, value: str) -> str:
        return normalize_base_path_value(value)


class StorageConnectionItem(BaseModel):
    id: int
    storage_id: str
    name: str
    protocol: str
    host: str
    port: int
    username: str
    base_path: str
    is_shared: bool
    is_active: bool
    created_by: int | None
    created_by_username: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StorageConnectionListResponse(BaseModel):
    items: list[StorageConnectionItem]
    total: int
    page: int
    page_size: int


class StorageEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int
    modified_at: str = ""


class StorageFileListResponse(BaseModel):
    path: str
    entries: list[StorageEntry]
    truncated: bool = False


class StorageMkdirRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1000)


class StorageRenameRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    new_name: str = Field(min_length=1, max_length=255)

    @field_validator("new_name")
    @classmethod
    def validate_new_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or cleaned in (".", "..") or any(char in cleaned for char in ENTRY_NAME_INVALID_CHARS):
            raise PydanticCustomError("validation.entryName", "Invalid file or directory name")
        return cleaned
