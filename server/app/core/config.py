from functools import lru_cache
import json
import os
from pathlib import Path
import re

from pydantic import BaseModel


PROJECT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseModel):
    app_name: str = "App"
    app_slug: str = "app"
    app_version: str = "0.1.0"
    token_expire_minutes: int = 12 * 60
    runtime_dir: Path = Path("runtime")

    @property
    def install_config_path(self) -> Path:
        return self.runtime_dir / "install.json"


@lru_cache
def get_settings() -> Settings:
    app_config = _load_app_config()
    app_name = _clean_name(os.getenv("APP_NAME")) or _clean_name(os.getenv("METRIX_APP_NAME")) or _clean_name(app_config.get("appName")) or "App"
    app_slug = _clean_slug(os.getenv("APP_SLUG")) or _clean_slug(os.getenv("METRIX_APP_SLUG")) or _clean_slug(app_config.get("appSlug")) or _slugify(app_name)
    runtime_dir = Path(os.getenv("METRIX_RUNTIME_DIR", "runtime"))
    return Settings(app_name=app_name, app_slug=app_slug, runtime_dir=runtime_dir)


def _load_app_config() -> dict[str, object]:
    try:
        return json.loads((PROJECT_DIR / "app.config.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _clean_name(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _clean_slug(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"(^_+|_+$)", "", re.sub(r"[^a-z0-9_]+", "_", value.strip().lower()))


def _slugify(value: str) -> str:
    return _clean_slug(value) or "app"
