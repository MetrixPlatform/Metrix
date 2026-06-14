from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


class DatabaseConnection(Base):
    __tablename__ = "db_connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conn_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    db_type: Mapped[str] = mapped_column(String(20), index=True)
    host: Mapped[str] = mapped_column(String(255))
    port: Mapped[int] = mapped_column(Integer)
    username: Mapped[str] = mapped_column(String(120))
    password_encrypted: Mapped[str] = mapped_column(String(512))
    default_database: Mapped[str] = mapped_column(String(128), default="", index=True)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class SqlScript(Base):
    __tablename__ = "sql_scripts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    content: Mapped[str] = mapped_column(Text)
    connection_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("db_connections.id"), nullable=True, index=True)
    database: Mapped[str] = mapped_column(String(128), default="", index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class DataJob(Base):
    __tablename__ = "data_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(20), index=True)
    connection_id: Mapped[int] = mapped_column(Integer, ForeignKey("db_connections.id"), index=True)
    format: Mapped[str] = mapped_column(String(20), index=True)
    params_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    file_name: Mapped[str] = mapped_column(String(255), default="")
    file_path: Mapped[str] = mapped_column(String(1000), default="")
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str] = mapped_column(String(120), default="")
    downloaded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
