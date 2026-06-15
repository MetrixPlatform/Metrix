from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class DockerUnavailableError(RuntimeError):
    pass


class DockerOperationError(RuntimeError):
    pass


class DockerAdapter:
    def __init__(self, client: Any):
        self.client = client

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

    def ensure_volume(self, name: str) -> None:
        try:
            self.client.volumes.get(name)
        except Exception:
            self.client.volumes.create(name=name, labels={"metrix.created_by": "metrix", "metrix.resource_type": "volume"})


def create_client() -> DockerAdapter:
    try:
        import docker
        from docker.errors import DockerException
    except Exception as exc:  # pragma: no cover - exercised when dependency is absent
        raise DockerUnavailableError("Docker SDK is not installed") from exc

    try:
        return DockerAdapter(docker.from_env())
    except DockerException as exc:
        raise DockerUnavailableError(str(exc)) from exc


def docker_host_label() -> str:
    return os.getenv("DOCKER_HOST", "from_env")
