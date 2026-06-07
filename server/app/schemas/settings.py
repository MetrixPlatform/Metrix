from typing import Literal

from pydantic import BaseModel, Field


LocaleCode = Literal["zh-CN", "en-US"]
LogRetentionDays = Literal[7, 30, 90, 180, 365]


class RegistrationRequiredFields(BaseModel):
    phone: bool = True
    email: bool = True
    company: bool = False
    department: bool = False


class PublicSettings(BaseModel):
    app_name: str
    registration_enabled: bool
    registration_required_fields: RegistrationRequiredFields
    default_locale: LocaleCode
    api_enabled: bool


class SystemSettings(PublicSettings):
    log_retention_days: LogRetentionDays


class SystemSettingsUpdate(BaseModel):
    app_name: str = Field(min_length=1, max_length=80)
    registration_enabled: bool
    registration_required_fields: RegistrationRequiredFields
    log_retention_days: LogRetentionDays
    default_locale: LocaleCode
    api_enabled: bool
