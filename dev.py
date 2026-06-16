"""Single-window dev launcher: runs backend and frontend together in one terminal.

Usage:
    python dev.py            # start backend (auto-reload) + frontend (HMR)

Logs from both services are merged into this window with [backend] / [web] prefixes.
Press Ctrl+C once to stop both services (including their child processes).
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IS_WINDOWS = os.name == "nt"
VENV_PYTHON = ROOT / ".venv" / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")

_processes: list[tuple[str, subprocess.Popen]] = []
_stopping = threading.Event()


def log(name: str, message: str) -> None:
    line = f"[{name}] {message}".rstrip("\r\n") + "\n"
    try:
        sys.stdout.write(line)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        sys.stdout.write(line.encode(encoding, "replace").decode(encoding, "replace"))
    sys.stdout.flush()


def _stream(name: str, process: subprocess.Popen) -> None:
    assert process.stdout is not None
    for raw in iter(process.stdout.readline, b""):
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        log(name, line)


def _spawn(name: str, args: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.Popen:
    kwargs: dict[str, object] = {
        "cwd": str(cwd),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "env": env,
    }
    if IS_WINDOWS:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(args, **kwargs)  # type: ignore[arg-type]
    _processes.append((name, process))
    threading.Thread(target=_stream, args=(name, process), daemon=True).start()
    return process


def _stop_all() -> None:
    if _stopping.is_set():
        return
    _stopping.set()
    for name, process in _processes:
        if process.poll() is not None:
            continue
        log(name, "stopping...")
        try:
            if IS_WINDOWS:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(process.pid)], capture_output=True, check=False)
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception:
            pass


def main() -> int:
    try:
        sys.stdout.reconfigure(errors="replace")  # tolerate non-encodable child output (e.g. GBK consoles)
    except Exception:
        pass

    if not VENV_PYTHON.exists():
        log("dev", f"Python venv not found: {VENV_PYTHON}")
        log("dev", "Create it first: python -m venv .venv && .venv/Scripts/python -m pip install -r server/requirements.txt")
        return 1

    web_dir = ROOT / "web"
    if not (web_dir / "node_modules").exists():
        npm = shutil.which("npm")
        if not npm:
            log("dev", "npm not found in PATH; install Node.js first")
            return 1
        log("web", "installing dependencies (first run)...")
        if subprocess.run([npm, "install"], cwd=str(web_dir), shell=IS_WINDOWS, check=False).returncode != 0:
            log("web", "npm install failed")
            return 1

    node = shutil.which("node")
    vite_bin = web_dir / "node_modules" / "vite" / "bin" / "vite.js"
    if not node or not vite_bin.exists():
        log("dev", "node or vite not found; run npm install in web/ first")
        return 1

    backend_env = {**os.environ, "METRIX_RELOAD": "1"}
    _spawn("backend", [str(VENV_PYTHON), "main.py"], ROOT / "server", backend_env)
    _spawn("web", [node, str(vite_bin), "--host", "127.0.0.1", "--port", "5173"], web_dir)

    log("backend", "starting -> http://127.0.0.1:8000 (auto-reload)")
    log("web", "starting -> http://127.0.0.1:5173 (hot reload)")
    log("dev", "press Ctrl+C to stop both services")

    try:
        while not _stopping.is_set():
            for name, process in _processes:
                code = process.poll()
                if code is not None:
                    log(name, f"exited with code {code}; shutting down the other service")
                    return code or 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        log("dev", "received Ctrl+C")
    finally:
        _stop_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
