from typing import Literal

from pydantic import BaseModel, Field


LocaleCode = Literal["zh-CN", "en-US"]
LogRetentionDays = Literal[7, 30, 90, 180, 365]
DockerConnectionMode = Literal["auto", "manual"]


class RegistrationRequiredFields(BaseModel):
    phone: bool = True
    email: bool = True
    company: bool = False
    department: bool = False


class PublicSettings(BaseModel):
    app_name: str
    registration_enabled: bool
    registration_approval_required: bool
    registration_required_fields: RegistrationRequiredFields
    default_locale: LocaleCode
    api_enabled: bool
    api_token_reveal_enabled: bool
    navigation_order: list[str] = Field(default_factory=list)


class SystemSettings(PublicSettings):
    log_retention_days: LogRetentionDays
    data_job_max_workers: int = Field(default=2, ge=1, le=16)
    data_job_retention_hours: int = Field(default=168, ge=1, le=8760)
    data_job_retention_days: int = Field(default=7, ge=1, le=365)
    docker_connection_mode: DockerConnectionMode = "auto"
    docker_host: str = Field(default="", max_length=300)


class SystemSettingsUpdate(BaseModel):
    app_name: str = Field(min_length=1, max_length=80)
    registration_enabled: bool
    registration_approval_required: bool
    registration_required_fields: RegistrationRequiredFields
    log_retention_days: LogRetentionDays
    default_locale: LocaleCode
    api_enabled: bool
    api_token_reveal_enabled: bool
    data_job_max_workers: int = Field(default=2, ge=1, le=16)
    data_job_retention_hours: int | None = Field(default=None, ge=1, le=8760)
    data_job_retention_days: int | None = Field(default=None, ge=1, le=365)
    navigation_order: list[str] = Field(default_factory=list, max_length=200)
    docker_connection_mode: DockerConnectionMode = "auto"
    docker_host: str = Field(default="", max_length=300)
