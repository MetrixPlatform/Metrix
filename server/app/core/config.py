from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Metrix"
    app_version: str = "0.1.0"
    token_expire_minutes: int = 12 * 60
    runtime_dir: Path = Path("runtime")

    @property
    def install_config_path(self) -> Path:
        return self.runtime_dir / "install.json"


@lru_cache
def get_settings() -> Settings:
    runtime_dir = Path(os.getenv("METRIX_RUNTIME_DIR", "runtime"))
    return Settings(runtime_dir=runtime_dir)
