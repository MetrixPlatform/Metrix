from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from app.core.config import get_settings


class InstallConfig(BaseModel):
    database_type: str
    database_url: str
    secret_key: str
    installed_at: str


def is_installed() -> bool:
    return get_settings().install_config_path.exists()


def load_install_config() -> InstallConfig:
    path = get_settings().install_config_path
    data = json.loads(path.read_text(encoding="utf-8"))
    return InstallConfig(**data)


def write_install_config(database_type: str, database_url: str) -> InstallConfig:
    settings = get_settings()
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    config = InstallConfig(
        database_type=database_type,
        database_url=database_url,
        secret_key=secrets.token_urlsafe(48),
        installed_at=datetime.now(timezone.utc).isoformat(),
    )
    settings.install_config_path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
    return config


def default_sqlite_path() -> Path:
    settings = get_settings()
    return settings.runtime_dir / f"{settings.app_slug}.db"
