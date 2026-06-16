from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

ScriptNetworkMode = Literal["none", "bridge"]
ScriptRunStatus = Literal["pending", "running", "success", "failed", "timeout", "canceled"]
ScriptScheduleTrigger = Literal["interval", "cron"]


class ScriptProjectPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    language: str = Field(default="python", min_length=1, max_length=40)
    base_image: str = Field(min_length=1, max_length=500)
    network_mode: ScriptNetworkMode = "bridge"
    is_shared: bool = False
    run_command: str = Field(default="", max_length=1000)
    env: dict[str, str] = Field(default_factory=dict)
    cpu_limit: float | None = Field(default=None, ge=0.1, le=256)
    memory_limit_mb: int | None = Field(default=None, ge=16, le=1048576)
    # 0 means no timeout limit.
    timeout_seconds: int = Field(default=0, ge=0, le=86400)

    @field_validator("name", "description", "language", "base_image", "run_command")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class ScriptProjectItem(BaseModel):
    id: int
    slug: str
    name: str
    description: str
    language: str
    base_image: str
    network_mode: str
    is_shared: bool = False
    run_command: str
    env: dict[str, str] = Field(default_factory=dict)
    cpu_limit: float | None = None
    memory_limit_mb: int | None = None
    timeout_seconds: int
    workspace_path: str = ""
    created_by: int | None = None
    created_by_username: str = ""
    created_at: datetime
    updated_at: datetime


class ScriptProjectListResponse(BaseModel):
    items: list[ScriptProjectItem]
    total: int
    page: int
    page_size: int


class PresetImageItem(BaseModel):
    image: str
    language: str
    run_command: str
    use_venv: bool
    available: bool


class LocalImageItem(BaseModel):
    image: str


class AvailableImagesResponse(BaseModel):
    presets: list[PresetImageItem]
    local_images: list[LocalImageItem]
    docker_available: bool
    message: str = ""


class ScriptFileEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: int = 0
    modified_at: str = ""


class ScriptFileListResponse(BaseModel):
    path: str
    entries: list[ScriptFileEntry]


class ScriptFileContent(BaseModel):
    path: str
    content: str
    truncated: bool = False


class ScriptFileWriteRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    content: str = Field(default="", max_length=5_000_000)


class ScriptPathRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1000)


class ScriptRenameRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1000)
    new_name: str = Field(min_length=1, max_length=255)


class ScriptRunItem(BaseModel):
    id: int
    run_id: str
    project_id: int
    trigger: str
    schedule_id: int | None = None
    status: str
    exit_code: int | None = None
    error_code: str = ""
    created_by: int | None = None
    created_by_username: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class ScriptRunListResponse(BaseModel):
    items: list[ScriptRunItem]
    total: int
    page: int
    page_size: int


class ScriptRunLog(BaseModel):
    run_id: str
    status: str
    logs: str


class RunSubmitResponse(BaseModel):
    run_id: str
    status: str


class ScriptSchedulePayload(BaseModel):
    name: str = Field(default="", max_length=120)
    trigger_type: ScriptScheduleTrigger = "interval"
    interval_seconds: int | None = Field(default=None, ge=10, le=2_592_000)
    cron_expr: str = Field(default="", max_length=120)
    enabled: bool = True

    @field_validator("name", "cron_expr")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class ScriptScheduleItem(BaseModel):
    id: int
    project_id: int
    name: str
    trigger_type: str
    interval_seconds: int | None = None
    cron_expr: str = ""
    enabled: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScriptEnvironmentInfo(BaseModel):
    available: bool
    image: str = ""
    os_type: str = ""
    architecture: str = ""
    language: str = ""
    language_version: str = ""
    packages: str = ""
    pip_index_configured: bool = False
    npm_registry_configured: bool = False
    go_proxy_configured: bool = False
    network_mode: str = ""
    message: str = ""
