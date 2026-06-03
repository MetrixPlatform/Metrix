from __future__ import annotations

import os
from pathlib import Path

import uvicorn


PROJECT_DIR = Path(__file__).resolve().parent.parent


def main() -> None:
    os.environ.setdefault("METRIX_RUNTIME_DIR", str(PROJECT_DIR / "runtime"))
    host = os.getenv("METRIX_HOST", "127.0.0.1")
    port = int(os.getenv("METRIX_PORT", "8000"))
    reload_enabled = os.getenv("METRIX_RELOAD", "").lower() in {"1", "true", "yes", "on"}
    uvicorn.run("app.main:app", host=host, port=port, reload=reload_enabled)


if __name__ == "__main__":
    main()
