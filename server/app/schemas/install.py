from typing import Literal

from pydantic import BaseModel, Field


class InstallStatusResponse(BaseModel):
    installed: bool
    database_type: str | None = None


class MysqlInstallConfig(BaseModel):
    host: str = Field(min_length=1, max_length=120)
    port: int = Field(default=3306, ge=1, le=65535)
    database: str = Field(min_length=1, max_length=64)
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(default="", max_length=256)


class InstallRequest(BaseModel):
    database_type: Literal["sqlite", "mysql"]
    sqlite_path: str = Field(default="", max_length=500)
    mysql: MysqlInstallConfig | None = None
    admin_username: str = Field(min_length=3, max_length=64)
    admin_password: str = Field(min_length=6, max_length=128)
    admin_full_name: str = Field(min_length=1, max_length=80)
    admin_company: str = Field(default="", max_length=120)
    admin_department: str = Field(default="", max_length=120)
