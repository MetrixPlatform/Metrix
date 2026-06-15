from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

CONN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_$]{1,128}$")


def clean_identifier(value: str, field_name: str = "identifier") -> str:
    cleaned = value.strip()
    if not IDENTIFIER_RE.fullmatch(cleaned):
        raise PydanticCustomError("validation.identifier", f"Invalid {field_name}")
    return cleaned


def clean_optional_identifier(value: str) -> str:
    cleaned = value.strip()
    if cleaned:
        clean_identifier(cleaned)
    return cleaned


class DatabaseConnectionPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    conn_id: str = Field(default="", max_length=64)
    db_type: Literal["mysql", "mariadb"]
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(default="", max_length=255)
    default_database: str = Field(default="", max_length=128)
    is_shared: bool = False
    is_active: bool = True

    @field_validator("name", "host", "username")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("conn_id")
    @classmethod
    def validate_conn_id(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned and not CONN_ID_RE.fullmatch(cleaned):
            raise PydanticCustomError("validation.connId", "Connection ID must be 3-64 letters, digits, - or _")
        return cleaned

    @field_validator("default_database")
    @classmethod
    def validate_default_database(cls, value: str) -> str:
        return clean_optional_identifier(value)


class DatabaseTestRequest(BaseModel):
    id: int | None = None
    db_type: Literal["mysql", "mariadb"]
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(ge=1, le=65535)
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(default="", max_length=255)
    default_database: str = Field(default="", max_length=128)

    @field_validator("host", "username")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("default_database")
    @classmethod
    def validate_default_database(cls, value: str) -> str:
        return clean_optional_identifier(value)


class DatabaseConnectionItem(BaseModel):
    id: int
    conn_id: str
    name: str
    db_type: str
    host: str
    port: int
    username: str
    default_database: str
    is_shared: bool
    is_active: bool
    created_by: int | None
    created_by_username: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DatabaseConnectionListResponse(BaseModel):
    items: list[DatabaseConnectionItem]
    total: int
    page: int
    page_size: int


class SchemaItem(BaseModel):
    name: str


class TableItem(BaseModel):
    name: str


class ColumnItem(BaseModel):
    name: str
    type: str
    nullable: bool = True
    default: Any = None
    primary_key: bool = False
    autoincrement: bool = False
    comment: str = ""


class TableDataResponse(BaseModel):
    columns: list[ColumnItem]
    primary_keys: list[str]
    rows: list[dict[str, Any]]
    total: int
    total_exact: bool = True
    page: int
    page_size: int


class QueryRequest(BaseModel):
    sql: str = Field(min_length=1)
    database: str = Field(default="", max_length=128)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=100, ge=1, le=1000)

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)


class QueryResponse(BaseModel):
    statement_type: Literal["read", "write"]
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 100
    affected_rows: int = 0


class RunScriptRequest(BaseModel):
    content: str = ""
    script_id: int | None = None
    database: str = Field(default="", max_length=128)
    stop_on_error: bool = True

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)


class ScriptStatementResult(BaseModel):
    index: int
    sql: str
    ok: bool
    message: str = ""
    affected_rows: int = 0
    columns: list[str] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)


class RunScriptResponse(BaseModel):
    results: list[ScriptStatementResult]
    stopped: bool = False


class RowCreateRequest(BaseModel):
    database: str = Field(default="", max_length=128)
    table: str = Field(min_length=1, max_length=128)
    values: dict[str, Any]

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)

    @field_validator("table")
    @classmethod
    def validate_table(cls, value: str) -> str:
        return clean_identifier(value, "table")


class RowUpdateRequest(RowCreateRequest):
    keys: dict[str, Any]


class RowDeleteRequest(BaseModel):
    database: str = Field(default="", max_length=128)
    table: str = Field(min_length=1, max_length=128)
    keys: dict[str, Any]

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)

    @field_validator("table")
    @classmethod
    def validate_table(cls, value: str) -> str:
        return clean_identifier(value, "table")


class ColumnDefinition(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: str = Field(default="VARCHAR(255)", min_length=1, max_length=120)
    nullable: bool = True
    primary_key: bool = False
    default: str = ""
    autoincrement: bool = False
    comment: str = Field(default="", max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_identifier(value, "column")


class CreateTableRequest(BaseModel):
    database: str = Field(default="", max_length=128)
    name: str = Field(min_length=1, max_length=128)
    columns: list[ColumnDefinition] = Field(min_length=1)
    if_not_exists: bool = True

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_identifier(value, "table")


class AlterTableAction(BaseModel):
    action: Literal["add_column", "drop_column", "modify_column"]
    column: ColumnDefinition | None = None
    name: str = Field(default="", max_length=128)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_optional_identifier(value)


class AlterTableRequest(BaseModel):
    database: str = Field(default="", max_length=128)
    actions: list[AlterTableAction] = Field(min_length=1)

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)


class RenameTableRequest(BaseModel):
    database: str = Field(default="", max_length=128)
    new_name: str = Field(min_length=1, max_length=128)

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)

    @field_validator("new_name")
    @classmethod
    def validate_new_name(cls, value: str) -> str:
        return clean_identifier(value, "table")


class SchemaCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    charset: str = Field(default="", max_length=40)
    collation: str = Field(default="", max_length=80)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_identifier(value, "schema")


class SchemaAlterRequest(BaseModel):
    charset: str = Field(default="", max_length=40)
    collation: str = Field(default="", max_length=80)


class ExportQuery(BaseModel):
    name: str = Field(default="", max_length=120)
    sql: str = Field(min_length=1)


class ExportRequest(BaseModel):
    format: Literal["csv", "xlsx", "sqlite", "sql"]
    database: str = Field(default="", max_length=128)
    tables: list[str] = Field(default_factory=list)
    sql: str = ""
    queries: list[ExportQuery] = Field(default_factory=list)

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)

    @field_validator("tables")
    @classmethod
    def validate_tables(cls, value: list[str]) -> list[str]:
        return [clean_identifier(item, "table") for item in value]


class ImportRequest(BaseModel):
    format: Literal["csv", "xlsx", "sqlite", "sql"]
    database: str = Field(default="", max_length=128)
    target_table: str = Field(default="", max_length=128)
    mode: Literal["append", "overwrite", "upsert"] = "append"
    mapping: dict[str, str] = Field(default_factory=dict)
    create_table: bool = False

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)

    @field_validator("target_table")
    @classmethod
    def validate_target_table(cls, value: str) -> str:
        return clean_optional_identifier(value)


class DatabaseTransferJobItem(BaseModel):
    id: int
    job_id: str
    kind: str
    connection_id: int
    conn_id: str = ""
    connection_name: str = ""
    created_by_username: str = ""
    format: str
    status: str
    file_name: str
    file_size: int
    row_count: int
    error_code: str
    created_by: int | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    expires_at: datetime | None
    downloaded_at: datetime | None

    model_config = {"from_attributes": True}


class DatabaseTransferJobListResponse(BaseModel):
    items: list[DatabaseTransferJobItem]
    total: int
    page: int
    page_size: int


class DatabaseTransferJobDownloadCount(BaseModel):
    count: int


class JobSubmitResponse(BaseModel):
    job_id: str
    status: str


class SqlScriptPayload(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1)
    connection_id: int | None = None
    database: str = Field(default="", max_length=128)
    description: str = Field(default="", max_length=500)
    is_shared: bool = False

    @field_validator("name", "description")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("database")
    @classmethod
    def validate_database(cls, value: str) -> str:
        return clean_optional_identifier(value)


class SqlScriptItem(BaseModel):
    id: int
    name: str
    content: str
    connection_id: int | None
    database: str = ""
    connection_name: str = ""
    description: str
    is_shared: bool
    created_by: int | None
    created_by_username: str = ""
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SqlScriptListResponse(BaseModel):
    items: list[SqlScriptItem]
    total: int
    page: int
    page_size: int
