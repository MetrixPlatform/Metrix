from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


ContainerStatus = Literal["created", "running", "paused", "restarting", "removing", "exited", "dead"]
ContainerRestartPolicy = Literal["no", "always", "unless-stopped", "on-failure"]


class ContainerEngineStatus(BaseModel):
    available: bool
    message: str = ""
    version: str = ""
    os_type: str = ""
    architecture: str = ""
    docker_host: str = ""
    containers: int = 0
    images: int = 0


class ContainerPortMapping(BaseModel):
    container_port: str = Field(min_length=1, max_length=32)
    host_port: int | None = Field(default=None, ge=1, le=65535)
    protocol: Literal["tcp", "udp"] = "tcp"


class ContainerVolumeMapping(BaseModel):
    container_path: str = Field(min_length=1, max_length=500)
    volume_name: str = Field(default="", max_length=120)
    read_only: bool = False

    @field_validator("container_path", "volume_name")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class ContainerCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    image: str = Field(min_length=1, max_length=500)
    command: str = Field(default="", max_length=1000)
    env: dict[str, str] = Field(default_factory=dict)
    ports: list[ContainerPortMapping] = Field(default_factory=list, max_length=20)
    volumes: list[ContainerVolumeMapping] = Field(default_factory=list, max_length=20)
    restart_policy: ContainerRestartPolicy = "no"
    memory_limit_mb: int | None = Field(default=None, ge=16, le=1048576)
    cpu_limit: float | None = Field(default=None, ge=0.1, le=256)
    auto_start: bool = False

    @field_validator("name", "image", "command")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()


class ContainerItem(BaseModel):
    id: str
    short_id: str
    name: str
    image: str
    status: str
    state: str
    ports: list[str] = Field(default_factory=list)
    labels: dict[str, str] = Field(default_factory=dict)
    created_at: str = ""
    owner_user_id: int | None = None
    owner_username: str = ""
    cpu_percent: float | None = None
    memory_usage: int | None = None
    memory_limit: int | None = None


class ContainerListResponse(BaseModel):
    items: list[ContainerItem]
    total: int
    page: int
    page_size: int


class ContainerLogsResponse(BaseModel):
    logs: str


class ContainerLogClearResult(BaseModel):
    cleared: bool
    restarted: bool
    requires_restart: bool


class ImageItem(BaseModel):
    id: str
    short_id: str
    repo_tags: list[str]
    size: int
    created_at: str = ""
    labels: dict[str, str] = Field(default_factory=dict)
    owner_user_id: int | None = None
    owner_username: str = ""
    is_public: bool = False
    source: str = ""


class ImageListResponse(BaseModel):
    items: list[ImageItem]
    total: int
    page: int
    page_size: int


class ImageVisibilityPayload(BaseModel):
    is_public: bool


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str


class ContainerJobItem(BaseModel):
    job_id: str
    kind: str
    image_ref: str
    status: str
    file_name: str
    file_size: int
    error_code: str = ""
    created_by: int | None
    created_by_username: str = ""
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class ContainerJobListResponse(BaseModel):
    items: list[ContainerJobItem]
    total: int
    page: int
    page_size: int
