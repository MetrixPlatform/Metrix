from __future__ import annotations

import json
import shlex
import threading
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, service_unavailable
from app.modules.containers import clients as docker_clients
from app.modules.containers.clients import DockerUnavailableError
from app.modules.scripts.models import ScriptProject
from app.modules.scripts.presets import PRESET_IMAGES
from app.modules.scripts.schemas import (
    AvailableImagesResponse,
    LocalImageItem,
    PresetImageItem,
    ScriptEnvironmentInfo,
)
from app.schemas.settings import SystemSettings
from app.services.settings import SettingService

METRIX_LABEL_CREATED_BY = "metrix.created_by"
METRIX_LABEL_OWNER = "metrix.owner_user_id"
METRIX_LABEL_RESOURCE = "metrix.resource_type"
METRIX_LABEL_PROJECT = "metrix.script_project_id"
METRIX_LABEL_RUN = "metrix.script_run_id"
METRIX_LABEL_VALUE = "metrix"
MAX_LOG_BYTES = 2 * 1024 * 1024
TERMINAL_KEEPALIVE = ["sh", "-c", "trap : TERM INT; sleep 86400 & wait"]


def docker_client_config(db: Session) -> docker_clients.DockerClientConfig:
    settings = SettingService(db).get_settings()
    return docker_clients.DockerClientConfig(mode=settings.docker_connection_mode, host=settings.docker_host)


def create_adapter(db: Session):
    try:
        return docker_clients.create_client(docker_client_config(db))
    except DockerUnavailableError as exc:
        raise service_unavailable("error.scriptDockerUnavailable", str(exc))


def ensure_image_available(adapter, image: str) -> None:
    try:
        adapter.get_image(image)
    except Exception:
        raise bad_request("error.scriptImageMissing", "Image not found locally", image=image)


def package_environment(settings: SystemSettings) -> dict[str, str]:
    # Inject package source env vars only when configured; empty means "use public source if online".
    env: dict[str, str] = {}
    if settings.script_pip_index_url:
        env["PIP_INDEX_URL"] = settings.script_pip_index_url
    if settings.script_pip_trusted_host:
        env["PIP_TRUSTED_HOST"] = settings.script_pip_trusted_host
    if settings.script_npm_registry:
        env["NPM_CONFIG_REGISTRY"] = settings.script_npm_registry
    if settings.script_go_proxy:
        env["GOPROXY"] = settings.script_go_proxy
    return env


def parse_project_env(value: str) -> dict[str, str]:
    try:
        data = json.loads(value or "{}")
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(item) for key, item in data.items()}


def terminal_environment(settings: SystemSettings, project: ScriptProject) -> dict[str, str]:
    # Terminal sessions get the package source vars, the project env vars, and a real
    # terminal type so the interactive shell has line editing and completion.
    env = package_environment(settings)
    env.update(parse_project_env(project.env))
    env.setdefault("TERM", "xterm-256color")
    env.setdefault("LANG", "C.UTF-8")
    return env


# VSCode-like default shell: prefer bash (readline history + tab completion), activate
# the project venv when present, fall back to sh for images without bash (e.g. alpine).
_DEFAULT_TERMINAL_SCRIPT = (
    "cd /workspace 2>/dev/null; "
    "[ -f .venv/bin/activate ] && . .venv/bin/activate 2>/dev/null; "
    "if command -v bash >/dev/null 2>&1; then exec bash; else exec sh; fi"
)


def _terminal_shell_command(custom: str) -> list[str]:
    text = (custom or "").strip()
    if text:
        try:
            return shlex.split(text)
        except ValueError:
            return text.split()
    return ["/bin/sh", "-c", _DEFAULT_TERMINAL_SCRIPT]


def list_available_images(db: Session) -> AvailableImagesResponse:
    try:
        adapter = create_adapter(db)
        tags = _local_image_tags(adapter)
    except Exception as exc:
        return AvailableImagesResponse(
            presets=[_preset_item(preset, False) for preset in PRESET_IMAGES],
            local_images=[],
            docker_available=False,
            message=str(exc),
        )
    local_set = set(tags)
    local = sorted({tag for tag in tags if "<none>" not in tag})
    return AvailableImagesResponse(
        presets=[_preset_item(preset, preset.image in local_set) for preset in PRESET_IMAGES],
        local_images=[LocalImageItem(image=tag) for tag in local],
        docker_available=True,
    )


def run_script(
    adapter,
    project: ScriptProject,
    host_workspace: Path,
    env: dict[str, str],
    log_path: Path,
    run_id: str = "",
) -> tuple[str, int | None]:
    ensure_image_available(adapter, project.base_image)
    raw = adapter.client
    container = raw.containers.run(**_run_kwargs(project, host_workspace, env, detach=True, run_id=run_id))
    timed_out = threading.Event()
    # timeout_seconds <= 0 means run with no timeout limit.
    timer = threading.Timer(project.timeout_seconds, lambda: _kill(container, timed_out)) if project.timeout_seconds > 0 else None
    if timer is not None:
        timer.start()
    try:
        _stream_logs(container, log_path)
        exit_code = _wait_exit_code(container)
    finally:
        if timer is not None:
            timer.cancel()
        _remove(container)
    if timed_out.is_set():
        return "timeout", exit_code
    return ("success" if exit_code == 0 else "failed"), exit_code


def open_terminal(db: Session, project: ScriptProject, host_workspace: Path, command: str, cols: int, rows: int):
    settings = SettingService(db).get_settings()
    adapter = create_adapter(db)
    ensure_image_available(adapter, project.base_image)
    raw = adapter.client
    kwargs = _run_kwargs(project, host_workspace, terminal_environment(settings, project), detach=True)
    kwargs["command"] = TERMINAL_KEEPALIVE
    kwargs["tty"] = True
    kwargs["stdin_open"] = True
    container = raw.containers.run(**kwargs)
    exec_id, sock, api = adapter.create_exec(container, _terminal_shell_command(command), "", cols, rows)
    return container, exec_id, sock, api


def environment_info(db: Session, project: ScriptProject, host_workspace: Path) -> ScriptEnvironmentInfo:
    settings = SettingService(db).get_settings()
    base = ScriptEnvironmentInfo(
        available=False,
        image=project.base_image,
        language=project.language,
        network_mode=project.network_mode,
        pip_index_configured=bool(settings.script_pip_index_url),
        npm_registry_configured=bool(settings.script_npm_registry),
        go_proxy_configured=bool(settings.script_go_proxy),
    )
    try:
        adapter = create_adapter(db)
    except Exception as exc:
        return base.model_copy(update={"message": str(exc)})
    try:
        image_obj = adapter.get_image(project.base_image)
    except Exception:
        return base.model_copy(update={"message": "error.scriptImageMissing"})
    attrs = getattr(image_obj, "attrs", {}) or {}
    raw = adapter.client
    output = ""
    try:
        result = raw.containers.run(
            image=project.base_image,
            command=["sh", "-c", _version_command(project.language)],
            remove=True,
            network_mode="none",
            working_dir="/workspace",
        )
        output = result.decode("utf-8", "replace") if isinstance(result, bytes) else str(result)
    except Exception as exc:
        output = str(exc)
    language_version, packages = _split_env_output(output)
    return base.model_copy(
        update={
            "available": True,
            "os_type": str(attrs.get("Os", "")),
            "architecture": str(attrs.get("Architecture", "")),
            "language_version": language_version,
            "packages": packages,
        }
    )


def run_labels(owner_user_id: int | None, project_id: int) -> dict[str, str]:
    return {
        METRIX_LABEL_CREATED_BY: METRIX_LABEL_VALUE,
        METRIX_LABEL_OWNER: str(owner_user_id) if owner_user_id is not None else "",
        METRIX_LABEL_RESOURCE: "script",
        METRIX_LABEL_PROJECT: str(project_id),
    }


def remove_project_containers(db: Session, project_id: int) -> None:
    # Best-effort cleanup of lingering run/terminal containers for a deleted project.
    # Never raises so project deletion still succeeds when Docker is unavailable.
    _remove_labeled_containers(db, f"{METRIX_LABEL_PROJECT}={project_id}")


def remove_run_container(db: Session, run_id: str) -> None:
    # Best-effort kill of a running script container so cancellation takes effect.
    _remove_labeled_containers(db, f"{METRIX_LABEL_RUN}={run_id}")


def _remove_labeled_containers(db: Session, label: str) -> None:
    try:
        adapter = create_adapter(db)
        raw = adapter.client
        containers = raw.containers.list(all=True, filters={"label": label})
    except Exception:
        return
    for container in containers:
        try:
            container.remove(force=True)
        except Exception:
            continue


def _run_kwargs(project: ScriptProject, host_workspace: Path, env: dict[str, str], detach: bool, run_id: str = "") -> dict[str, Any]:
    labels = run_labels(project.created_by, project.id)
    if run_id:
        labels[METRIX_LABEL_RUN] = run_id
    kwargs: dict[str, Any] = {
        "image": project.base_image,
        "detach": detach,
        "working_dir": "/workspace",
        "volumes": {str(host_workspace): {"bind": "/workspace", "mode": "rw"}},
        "network_mode": project.network_mode or "bridge",
        "environment": env,
        "labels": labels,
    }
    command = _run_command(project.run_command)
    if command:
        kwargs["command"] = command
    if project.memory_limit_mb:
        kwargs["mem_limit"] = f"{project.memory_limit_mb}m"
    if project.cpu_limit:
        kwargs["nano_cpus"] = int(project.cpu_limit * 1_000_000_000)
    return kwargs


def _run_command(run_command: str) -> list[str] | None:
    text = (run_command or "").strip()
    if not text:
        return None
    # Auto-use a workspace virtualenv when present (mirrors the terminal default shell), so deps
    # installed into /workspace/.venv are used for manual/scheduled runs without changing the run
    # command. When there is no .venv it just runs the command directly with the image's python.
    script = (
        "cd /workspace 2>/dev/null; "
        "[ -f .venv/bin/activate ] && . .venv/bin/activate 2>/dev/null; "
        f"{text}"
    )
    return ["/bin/sh", "-c", script]


def _stream_logs(container, log_path: Path) -> None:
    written = 0
    try:
        with log_path.open("wb") as log_file:
            for chunk in container.logs(stream=True, follow=True):
                if not isinstance(chunk, bytes):
                    chunk = str(chunk).encode("utf-8", "replace")
                if written < MAX_LOG_BYTES:
                    log_file.write(chunk[: MAX_LOG_BYTES - written])
                    written += len(chunk)
    except Exception:
        pass


def _wait_exit_code(container) -> int | None:
    try:
        result = container.wait()
    except Exception:
        return None
    if isinstance(result, dict):
        return result.get("StatusCode")
    try:
        return int(result)
    except (TypeError, ValueError):
        return None


def _kill(container, timed_out: threading.Event) -> None:
    timed_out.set()
    try:
        container.kill()
    except Exception:
        pass


def _remove(container) -> None:
    try:
        container.remove(force=True)
    except Exception:
        pass


def _local_image_tags(adapter) -> list[str]:
    tags: list[str] = []
    for image in adapter.list_images():
        repo_tags = getattr(image, "tags", None) or (getattr(image, "attrs", {}) or {}).get("RepoTags") or []
        tags.extend(str(tag) for tag in repo_tags)
    return tags


def _preset_item(preset, available: bool) -> PresetImageItem:
    return PresetImageItem(
        image=preset.image,
        language=preset.language,
        run_command=preset.run_command,
        use_venv=preset.use_venv,
        available=available,
    )


def _version_command(language: str) -> str:
    if language == "python":
        return "python --version 2>&1; echo '---'; pip list 2>/dev/null"
    if language == "node":
        return "node --version 2>&1; echo '---'; npm ls -g --depth=0 2>/dev/null"
    if language == "go":
        return "go version 2>&1; echo '---'"
    return "sh --version 2>&1 | head -n 1; echo '---'"


def _split_env_output(output: str) -> tuple[str, str]:
    if "---" in output:
        version, _, packages = output.partition("---")
        return version.strip(), packages.strip()
    return output.strip(), ""
