from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.time import utc_now
from app.db.base import Base


class ScriptProject(Base):
    __tablename__ = "script_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(String(500), default="")
    language: Mapped[str] = mapped_column(String(40), default="python", index=True)
    base_image: Mapped[str] = mapped_column(String(500), default="")
    network_mode: Mapped[str] = mapped_column(String(20), default="bridge")
    run_command: Mapped[str] = mapped_column(String(1000), default="")
    env: Mapped[str] = mapped_column(Text, default="{}")
    cpu_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_limit_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=600)
    workspace_path: Mapped[str] = mapped_column(String(1000), default="")
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)


class ScriptRun(Base):
    __tablename__ = "script_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("script_projects.id"), index=True)
    trigger: Mapped[str] = mapped_column(String(20), default="manual", index=True)
    schedule_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    exit_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    log_path: Mapped[str] = mapped_column(String(1000), default="")
    error_code: Mapped[str] = mapped_column(String(120), default="")
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ScriptSchedule(Base):
    __tablename__ = "script_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("script_projects.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    trigger_type: Mapped[str] = mapped_column(String(20), default="interval")
    interval_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cron_expr: Mapped[str] = mapped_column(String(120), default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)
