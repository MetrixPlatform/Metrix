"""Single-window dev launcher: runs Metrix + CapacityReport backends and frontends together.

Usage:
    python dev.py            # start all services with auto-reload / HMR

Starts up to four processes and merges their logs into this window:
  [backend]  Metrix API          http://127.0.0.1:8000  (auto-reload)
  [web]      Metrix web          http://127.0.0.1:5173  (vite HMR)
  [capa-api] CapacityReport API  http://127.0.0.1:9081  (auto-reload, own venv)
  [capa-web] CapacityReport web  http://127.0.0.1:5174  (vite HMR)
CapacityReport is the optional submodule under CapacityReport/; it is skipped if absent and
its failures never stop the Metrix services. Press Ctrl+C once to stop everything.
"""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IS_WINDOWS = os.name == "nt"
VENV_PYTHON = ROOT / ".venv" / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")
BACKEND_HOST = os.environ.get("METRIX_HOST", "127.0.0.1")
try:
    BACKEND_PORT = int(os.environ.get("METRIX_PORT", "8000"))
except ValueError:
    BACKEND_PORT = 8000

CAPA_DIR = ROOT / "CapacityReport"
CAPA_VENV_PYTHON = CAPA_DIR / ".venv" / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")
CAPA_BACKEND_PORT = 9081
CAPA_WEB_PORT = 5174

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


def _wait_for_http(proc_name: str, url: str, timeout: float = 60.0) -> bool:
    """Block until `url` answers HTTP, so a frontend (and the browser it serves) does not
    fire requests at a backend that has not finished starting (avoids the startup
    ECONNREFUSED flood on /api/install/status, /api/auth/me, etc.)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _stopping.is_set():
            return False
        if any(name == proc_name and proc.poll() is not None for name, proc in _processes):
            return False
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except urllib.error.HTTPError:
            return True  # any HTTP status means the ASGI app is serving
        except (urllib.error.URLError, OSError):
            time.sleep(0.4)
    return False


def _ensure_capa_venv() -> Path | None:
    """Return the CapacityReport venv python, creating the venv and installing requirements
    on first run. Returns None when the submodule is absent or setup fails, so CapacityReport
    is skipped without affecting the Metrix services."""
    if not CAPA_DIR.exists():
        return None
    if CAPA_VENV_PYTHON.exists():
        return CAPA_VENV_PYTHON
    log("capa-api", "creating venv (first run)...")
    if subprocess.run([str(VENV_PYTHON), "-m", "venv", str(CAPA_DIR / ".venv")], check=False).returncode != 0:
        log("capa-api", "venv creation failed; skipping CapacityReport backend")
        return None
    log("capa-api", "installing requirements (first run, may take a while)...")
    if subprocess.run(
        [str(CAPA_VENV_PYTHON), "-m", "pip", "install", "-r", str(CAPA_DIR / "requirements.txt")],
        cwd=str(CAPA_DIR),
        check=False,
    ).returncode != 0:
        log("capa-api", "pip install failed; skipping CapacityReport backend")
        return None
    return CAPA_VENV_PYTHON


def _start_capacity_report(node: str | None) -> None:
    """Start the optional CapacityReport submodule: backend :9081 (own venv) + web :5174.
    Anything missing is logged and skipped without affecting the Metrix services."""
    capa_python = _ensure_capa_venv()
    if capa_python is None:
        log("capa-api", f"CapacityReport submodule not set up at {CAPA_DIR}; skipping")
        return

    _spawn(
        "capa-api",
        [str(capa_python), "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", str(CAPA_BACKEND_PORT)],
        CAPA_DIR,
    )
    log("capa-api", f"starting -> http://127.0.0.1:{CAPA_BACKEND_PORT} (auto-reload)")

    capa_web_dir = CAPA_DIR / "frontend"
    capa_vite = capa_web_dir / "node_modules" / "vite" / "bin" / "vite.js"
    if not capa_vite.exists():
        npm = shutil.which("npm")
        if npm:
            log("capa-web", "installing dependencies (first run)...")
            subprocess.run([npm, "install"], cwd=str(capa_web_dir), shell=IS_WINDOWS, check=False)
    if not node or not capa_vite.exists():
        log("capa-web", "node or vite not found; skipping CapacityReport frontend")
        return

    # Let the API answer before the frontend so opening :5174 early does not flood proxy errors.
    if _wait_for_http("capa-api", f"http://127.0.0.1:{CAPA_BACKEND_PORT}/health", timeout=90.0):
        log("capa-web", "backend ready")
    _spawn("capa-web", [node, str(capa_vite), "--host", "127.0.0.1", "--port", str(CAPA_WEB_PORT)], capa_web_dir)
    log("capa-web", f"starting -> http://127.0.0.1:{CAPA_WEB_PORT} (hot reload)")


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
    backend_proc = _spawn("backend", [str(VENV_PYTHON), "main.py"], ROOT / "server", backend_env)
    log("backend", f"starting -> http://{BACKEND_HOST}:{BACKEND_PORT} (auto-reload)")

    # Start the frontend only after the backend is serving, so the browser does not hit
    # a cold backend and flood the console with proxy ECONNREFUSED errors.
    log("web", "waiting for backend to be ready...")
    if _wait_for_http("backend", f"http://{BACKEND_HOST}:{BACKEND_PORT}/api/health"):
        log("web", "backend ready")
    elif not _stopping.is_set():
        log("web", "backend not ready in time; starting frontend anyway")
    if _stopping.is_set():
        return 0
    if backend_proc.poll() is not None:
        log("backend", f"exited with code {backend_proc.poll()} during startup")
        return backend_proc.poll() or 0

    _spawn("web", [node, str(vite_bin), "--host", "127.0.0.1", "--port", "5173"], web_dir)
    log("web", "starting -> http://127.0.0.1:5173 (hot reload)")

    _start_capacity_report(node)
    log("dev", "press Ctrl+C to stop all services")

    critical = {"backend", "web"}
    reported: set[str] = set()
    try:
        while not _stopping.is_set():
            for name, process in _processes:
                code = process.poll()
                if code is None or name in reported:
                    continue
                reported.add(name)
                if name in critical:
                    log(name, f"exited with code {code}; shutting down all services")
                    return code or 0
                log(name, f"exited with code {code}; other services keep running")
            time.sleep(0.5)
    except KeyboardInterrupt:
        log("dev", "received Ctrl+C")
    finally:
        _stop_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
