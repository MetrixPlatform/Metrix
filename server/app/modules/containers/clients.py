from __future__ import annotations

import os
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class DockerUnavailableError(RuntimeError):
    pass


class DockerOperationError(RuntimeError):
    pass


@dataclass(frozen=True)
class DockerClientConfig:
    mode: str = "auto"
    host: str = ""


@dataclass(frozen=True)
class DockerHostCandidate:
    label: str
    base_url: str
    use_env: bool = False


class DockerAdapter:
    def __init__(self, client: Any, host_label: str = ""):
        self.client = client
        self.host_label = host_label

    def ping(self) -> None:
        self.client.ping()

    def info(self) -> dict[str, Any]:
        return self.client.info()

    def version(self) -> dict[str, Any]:
        return self.client.version()

    def list_containers(self) -> list[Any]:
        return self.client.containers.list(all=True)

    def get_container(self, container_id: str) -> Any:
        return self.client.containers.get(container_id)

    def create_container(
        self,
        name: str,
        image: str,
        command: str,
        environment: dict[str, str],
        labels: dict[str, str],
        ports: dict[str, int | None],
        volumes: dict[str, dict[str, str]],
        restart_policy: dict[str, str],
        mem_limit: str | None,
        nano_cpus: int | None,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "image": image,
            "name": name,
            "detach": True,
            "environment": environment,
            "labels": labels,
            "ports": ports or None,
            "volumes": volumes or None,
            "restart_policy": restart_policy,
            "network_mode": "bridge",
        }
        if command:
            kwargs["command"] = command
        if mem_limit:
            kwargs["mem_limit"] = mem_limit
        if nano_cpus:
            kwargs["nano_cpus"] = nano_cpus
        return self.client.containers.create(**kwargs)

    def list_images(self) -> list[Any]:
        return self.client.images.list()

    def get_image(self, image_ref: str) -> Any:
        return self.client.images.get(image_ref)

    def remove_image(self, image_ref: str) -> None:
        self.client.images.remove(image_ref, force=False, noprune=False)

    def load_image(self, path: Path) -> list[Any]:
        with path.open("rb") as source:
            return self.client.images.load(source.read())

    def save_image(self, image_ref: str) -> Iterator[bytes]:
        image = self.get_image(image_ref)
        yield from image.save(named=True)

    def list_volumes(self) -> list[Any]:
        return self.client.volumes.list()

    def get_volume(self, name: str) -> Any:
        return self.client.volumes.get(name)

    def create_volume(self, name: str, driver: str = "local", labels: dict[str, str] | None = None) -> Any:
        return self.client.volumes.create(name=name, driver=driver or "local", labels=labels or {})

    def remove_volume(self, name: str, force: bool = False) -> None:
        self.get_volume(name).remove(force=force)

    def ensure_volume(self, name: str, labels: dict[str, str] | None = None) -> Any:
        try:
            return self.get_volume(name)
        except Exception:
            return self.create_volume(
                name,
                labels=labels or {"metrix.created_by": "metrix", "metrix.resource_type": "volume"},
            )

    def create_exec(self, container: Any, command: list[str], user: str, cols: int, rows: int) -> tuple[str, Any, Any]:
        api = container.client.api
        exec_id = api.exec_create(
            container.id,
            command,
            tty=True,
            stdin=True,
            stdout=True,
            stderr=True,
            user=user or "",
        )["Id"]
        sock = api.exec_start(exec_id, tty=True, socket=True)
        raw = getattr(sock, "_sock", None) or sock
        if cols and rows:
            try:
                api.exec_resize(exec_id, height=rows, width=cols)
            except Exception:
                pass
        return exec_id, raw, api

    def truncate_container_log(self, container: Any) -> None:
        attrs = getattr(container, "attrs", {}) or {}
        log_path = attrs.get("LogPath") or ""
        if not log_path:
            raise DockerOperationError("Container has no log file")
        image_id = attrs.get("Image") or getattr(getattr(container, "image", None), "id", "")
        if not image_id:
            raise DockerOperationError("Container image not found")
        # A helper container running inside the daemon truncates the json log file in place.
        # The platform host cannot reach the daemon log path directly (e.g. Docker Desktop VM),
        # so we mount the daemon container dir and truncate from within.
        self.client.containers.run(
            image=image_id,
            entrypoint=["/bin/sh", "-c", 'truncate -s 0 "$1" 2>/dev/null || : > "$1"', "sh", log_path],
            remove=True,
            network_mode="none",
            user="0:0",
            volumes={"/var/lib/docker/containers": {"bind": "/var/lib/docker/containers", "mode": "rw"}},
        )


def create_client(config: DockerClientConfig | None = None) -> DockerAdapter:
    try:
        import docker
        from docker.errors import DockerException
    except Exception as exc:  # pragma: no cover - exercised when dependency is absent
        raise DockerUnavailableError("Docker SDK is not installed") from exc

    errors: list[str] = []
    for candidate in docker_host_candidates(config):
        try:
            client = docker.from_env(timeout=3) if candidate.use_env else docker.DockerClient(base_url=candidate.base_url, timeout=3)
            adapter = DockerAdapter(client, candidate.label)
            adapter.ping()
            return adapter
        except DockerException as exc:
            errors.append(f"{candidate.label}: {exc}")
        except Exception as exc:
            errors.append(f"{candidate.label}: {exc}")
    raise DockerUnavailableError("; ".join(errors) or "No Docker host candidates available")


def docker_host_label(config: DockerClientConfig | None = None) -> str:
    if config and config.mode == "manual":
        return config.host.strip() or "manual"
    candidates = docker_host_candidates(config)
    if candidates:
        return "auto"
    return "auto"


def docker_host_candidates(config: DockerClientConfig | None = None) -> list[DockerHostCandidate]:
    if config and config.mode == "manual":
        host = config.host.strip()
        return [DockerHostCandidate(host, host)] if host else []

    candidates: list[DockerHostCandidate] = []
    env_host = os.getenv("DOCKER_HOST", "").strip()
    if env_host:
        candidates.append(DockerHostCandidate(env_host, env_host, use_env=True))

    for path in ("/var/run/docker.sock", "/run/docker.sock"):
        if Path(path).exists():
            candidates.append(DockerHostCandidate(f"unix://{path}", f"unix://{path}"))

    if os.name == "nt":
        candidates.append(DockerHostCandidate("npipe:////./pipe/docker_engine", "npipe:////./pipe/docker_engine"))

    candidates.extend(
        [
            DockerHostCandidate("tcp://localhost:2375", "tcp://localhost:2375"),
            DockerHostCandidate("tcp://127.0.0.1:2375", "tcp://127.0.0.1:2375"),
        ]
    )
    return _dedupe_candidates(candidates)


def _dedupe_candidates(candidates: list[DockerHostCandidate]) -> list[DockerHostCandidate]:
    result: list[DockerHostCandidate] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = candidate.label.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(candidate)
    return result
