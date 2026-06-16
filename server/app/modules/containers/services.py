from __future__ import annotations

import json
import re
import shutil
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import PROJECT_DIR
from app.core.exceptions import bad_request, forbidden, not_found, service_unavailable
from app.core.time import utc_now
from app.db.session import get_session_factory
from app.models import User
from app.modules.containers import CONTAINER_MANAGE_OTHERS
from app.modules.containers import clients as docker_clients
from app.modules.containers.clients import DockerOperationError, DockerUnavailableError
from app.modules.containers.models import ContainerJob
from app.modules.containers.repositories import ContainerImageRepository, ContainerJobRepository
from app.modules.containers.schemas import (
    ContainerCreatePayload,
    ContainerEngineStatus,
    ContainerItem,
    ContainerJobItem,
    ContainerJobListResponse,
    ContainerListResponse,
    ContainerLogClearResult,
    ImageItem,
    ImageListResponse,
    JobSubmitResponse,
)
from app.services.audit import audit_detail, record_audit
from app.services.permissions import has_permission
from app.services.settings import SettingService

METRIX_LABEL_CREATED_BY = "metrix.created_by"
METRIX_LABEL_OWNER = "metrix.owner_user_id"
METRIX_LABEL_RESOURCE = "metrix.resource_type"
METRIX_LABEL_VALUE = "metrix"
CONTAINER_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$")
VOLUME_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,119}$")
SENSITIVE_KEY_RE = re.compile(r"(password|passwd|pwd|secret|token|key)", re.I)

_executor_lock = threading.Lock()
_executor: ThreadPoolExecutor | None = None


class ContainerService:
    def __init__(self, db: Session):
        self.db = db
        self.images = ContainerImageRepository(db)
        self.jobs = ContainerJobRepository(db)

    def engine_status(self) -> ContainerEngineStatus:
        config = _docker_client_config(self.db)
        try:
            client = docker_clients.create_client(config)
            client.ping()
            info = client.info()
            version = client.version()
            return ContainerEngineStatus(
                available=True,
                version=str(version.get("Version", "")),
                os_type=str(info.get("OSType", "")),
                architecture=str(info.get("Architecture", "")),
                docker_host=client.host_label,
                containers=int(info.get("Containers", 0) or 0),
                images=int(info.get("Images", 0) or 0),
            )
        except DockerUnavailableError as exc:
            return ContainerEngineStatus(available=False, message=str(exc), docker_host=docker_clients.docker_host_label(config))
        except Exception as exc:
            return ContainerEngineStatus(available=False, message=str(exc), docker_host=docker_clients.docker_host_label(config))

    def list_containers(
        self,
        actor: User,
        keyword: str = "",
        status: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> ContainerListResponse:
        pairs = [(raw, _container_item(raw)) for raw in self._client().list_containers()]
        if not has_permission(actor, CONTAINER_MANAGE_OTHERS):
            pairs = [pair for pair in pairs if pair[1].owner_user_id == actor.id]
        if keyword:
            needle = keyword.lower()
            pairs = [pair for pair in pairs if needle in pair[1].name.lower() or needle in pair[1].image.lower() or needle in pair[1].id.lower()]
        if status:
            pairs = [pair for pair in pairs if pair[1].status == status or pair[1].state == status]
        pairs.sort(key=lambda pair: pair[1].name.lower())
        total = len(pairs)
        page_pairs = pairs[(page - 1) * page_size : page * page_size]
        items = _attach_container_stats(page_pairs)
        return ContainerListResponse(items=self._with_container_usernames(items), total=total, page=page, page_size=page_size)

    def create_container(self, actor: User, payload: ContainerCreatePayload) -> ContainerItem:
        self._validate_container_payload(payload)
        image = self._get_visible_image(actor, payload.image)
        safe_name = _safe_container_name(actor.id, payload.name)
        client = self._client()
        volumes = {}
        for mapping in payload.volumes:
            volume_name = mapping.volume_name or f"metrix-u{actor.id}-{uuid.uuid4().hex[:8]}"
            client.ensure_volume(volume_name)
            volumes[volume_name] = {"bind": mapping.container_path, "mode": "ro" if mapping.read_only else "rw"}
        container = client.create_container(
            safe_name,
            image.id,
            payload.command,
            _safe_environment(payload.env),
            {
                METRIX_LABEL_CREATED_BY: METRIX_LABEL_VALUE,
                METRIX_LABEL_OWNER: str(actor.id),
                METRIX_LABEL_RESOURCE: "container",
            },
            {f"{item.container_port}/{item.protocol}": item.host_port for item in payload.ports},
            volumes,
            {"Name": payload.restart_policy},
            f"{payload.memory_limit_mb}m" if payload.memory_limit_mb else None,
            int(payload.cpu_limit * 1_000_000_000) if payload.cpu_limit else None,
        )
        if payload.auto_start:
            container.start()
        item = _container_item(container)
        record_audit(
            self.db,
            actor.id,
            "container.create",
            "container",
            item.id,
            item.name,
            audit_detail(item.name, meta={"image": image.repo_tags[0] if image.repo_tags else image.id}),
        )
        self.db.commit()
        return self._with_container_usernames([item])[0]

    def operate_container(self, actor: User, container_id: str, action: str) -> None:
        container = self._get_visible_container(actor, container_id)
        if action == "start":
            container.start()
        elif action == "stop":
            container.stop()
        elif action == "restart":
            container.restart()
        else:
            raise bad_request("error.containerActionInvalid", "Invalid container action")
        record_audit(self.db, actor.id, f"container.{action}", "container", container.id, _container_name(container))
        self.db.commit()

    def delete_container(self, actor: User, container_id: str, force: bool = False) -> None:
        container = self._get_visible_container(actor, container_id)
        name = _container_name(container)
        container.remove(force=force)
        record_audit(self.db, actor.id, "container.delete", "container", container_id, name)
        self.db.commit()

    def logs(self, actor: User, container_id: str, tail: int = 200) -> str:
        container = self._get_visible_container(actor, container_id)
        output = container.logs(tail=max(1, min(tail, 5000)))
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="replace")
        return str(output)

    def clear_logs(self, actor: User, container_id: str, restart: bool = False) -> ContainerLogClearResult:
        container = self._get_visible_container(actor, container_id)
        running = bool((getattr(container, "attrs", {}) or {}).get("State", {}).get("Running", False))
        # Truncating a running container's log corrupts the json-file reader, so it must be
        # stopped first; that needs a restart, which we confirm with the user before doing it.
        if running and not restart:
            return ContainerLogClearResult(cleared=False, restarted=False, requires_restart=True)
        try:
            if running:
                container.stop()
            docker_clients.DockerAdapter(getattr(container, "client", None)).truncate_container_log(container)
            if running:
                container.start()
        except Exception as exc:
            if running:
                try:
                    container.start()
                except Exception:
                    pass
            raise bad_request("error.containerLogClearFailed", "Failed to clear container logs") from exc
        record_audit(self.db, actor.id, "container.clear_logs", "container", container.id, _container_name(container))
        self.db.commit()
        return ContainerLogClearResult(cleared=True, restarted=running, requires_restart=False)

    def list_images(self, actor: User, keyword: str = "", page: int = 1, page_size: int = 20) -> ImageListResponse:
        images = [_image_item(item) for item in self._client().list_images()]
        image_ids = [item.id for item in images]
        visible_to = None if has_permission(actor, CONTAINER_MANAGE_OTHERS) else actor.id
        records = self.images.list(image_ids, visible_to)
        by_image: dict[str, list] = {}
        for record in records:
            by_image.setdefault(record.image_id, []).append(record)
        visible_items: list[ImageItem] = []
        for item in images:
            matched = by_image.get(item.id, [])
            if matched:
                owner = matched[0]
                item.owner_user_id = owner.created_by
                item.is_public = any(record.is_public for record in matched)
                item.source = owner.source
            else:
                item.is_public = True
                item.source = "docker"
            visible_items.append(item)
        if keyword:
            needle = keyword.lower()
            visible_items = [
                item for item in visible_items if needle in item.id.lower() or any(needle in tag.lower() for tag in item.repo_tags)
            ]
        visible_items.sort(key=lambda item: ",".join(item.repo_tags).lower() or item.id)
        total = len(visible_items)
        items = visible_items[(page - 1) * page_size : page * page_size]
        return ImageListResponse(items=self._with_image_usernames(items), total=total, page=page, page_size=page_size)

    def set_image_public(self, actor: User, image_ref: str, is_public: bool) -> ImageItem:
        if not has_permission(actor, CONTAINER_MANAGE_OTHERS):
            raise forbidden()
        image = self._image_by_ref(image_ref)
        record = self.images.get_for_image(image.id)
        if record is None:
            record = self.images.upsert(image.id, json.dumps(image.repo_tags, ensure_ascii=False), actor.id, "manual")
        record.is_public = is_public
        record_audit(self.db, actor.id, "container.image_visibility", "container_image", image.id, image.repo_tags[0] if image.repo_tags else image.id)
        self.db.commit()
        image.is_public = is_public
        image.owner_user_id = record.created_by
        return self._with_image_usernames([image])[0]

    def delete_image(self, actor: User, image_ref: str) -> None:
        image = self._get_visible_image(actor, image_ref)
        if self._image_used_by_visible_containers(actor, image.id):
            raise bad_request("error.containerImageInUse", "Image is in use")
        if not has_permission(actor, CONTAINER_MANAGE_OTHERS):
            record = self.images.get_owned(image.id, actor.id)
            if record is None:
                raise forbidden()
        self._client().remove_image(image.id)
        self.images.delete_for_image(image.id, None if has_permission(actor, CONTAINER_MANAGE_OTHERS) else actor.id)
        record_audit(self.db, actor.id, "container.image_delete", "container_image", image.id, image.repo_tags[0] if image.repo_tags else image.id)
        self.db.commit()

    def submit_import(self, actor: User, file: UploadFile) -> JobSubmitResponse:
        job_id = uuid.uuid4().hex
        path = _imports_dir() / f"{job_id}.tar"
        with path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
        job = self.jobs.create(
            ContainerJob(
                job_id=job_id,
                kind="import",
                status="pending",
                file_name=file.filename or path.name,
                file_path=str(path),
                file_size=path.stat().st_size,
                created_by=actor.id,
            )
        )
        record_audit(self.db, actor.id, "container.image_import_submit", "container_job", job.job_id, job.file_name)
        self.db.commit()
        _pool().submit(_run_job, job_id)
        return JobSubmitResponse(job_id=job_id, status="pending")

    def submit_export(self, actor: User, image_ref: str) -> JobSubmitResponse:
        image = self._get_visible_image(actor, image_ref)
        job_id = uuid.uuid4().hex
        safe_name = _safe_file_name((image.repo_tags[0] if image.repo_tags else image.short_id).replace(":", "_"))
        path = _exports_dir() / f"{job_id}.tar"
        job = self.jobs.create(
            ContainerJob(
                job_id=job_id,
                kind="export",
                image_ref=image.id,
                status="pending",
                file_name=f"{safe_name or 'image'}.tar",
                file_path=str(path),
                created_by=actor.id,
            )
        )
        record_audit(self.db, actor.id, "container.image_export_submit", "container_job", job.job_id, job.file_name)
        self.db.commit()
        _pool().submit(_run_job, job_id)
        return JobSubmitResponse(job_id=job_id, status="pending")

    def list_jobs(
        self,
        actor: User,
        keyword: str = "",
        kind: str = "",
        status: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> ContainerJobListResponse:
        visible_to = None if has_permission(actor, CONTAINER_MANAGE_OTHERS) else actor.id
        rows, total = self.jobs.list(keyword, kind, status, visible_to, "ascend" if sort_order == "ascend" else "descend", page, page_size)
        usernames = self.jobs.creator_usernames({row.created_by for row in rows if row.created_by is not None})
        return ContainerJobListResponse(
            items=[ContainerJobItem.model_validate(row).model_copy(update={"created_by_username": usernames.get(row.created_by, "")}) for row in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    def download_job(self, actor: User, job_id: str) -> tuple[str, BinaryIO]:
        job = self._get_visible_job(actor, job_id)
        if job.kind != "export" or job.status != "success":
            raise bad_request("error.containerJobNotDownloadable", "Container job is not downloadable")
        path = Path(job.file_path)
        if not path.is_file():
            raise not_found("error.containerJobFileMissing", "Container job file missing")
        return job.file_name, path.open("rb")

    def _get_visible_job(self, actor: User, job_id: str) -> ContainerJob:
        job = self.jobs.get(job_id)
        if job is None:
            raise not_found()
        if job.created_by == actor.id or has_permission(actor, CONTAINER_MANAGE_OTHERS):
            return job
        raise forbidden()

    def _client(self):
        try:
            return docker_clients.create_client(_docker_client_config(self.db))
        except DockerUnavailableError as exc:
            raise service_unavailable("error.containerDockerUnavailable", str(exc))

    def _get_visible_container(self, actor: User, container_id: str):
        try:
            container = self._client().get_container(container_id)
        except Exception:
            raise not_found("error.containerNotFound", "Container not found")
        owner = _container_owner(container)
        if owner == actor.id or has_permission(actor, CONTAINER_MANAGE_OTHERS):
            return container
        raise forbidden()

    def _image_by_ref(self, image_ref: str) -> ImageItem:
        try:
            return _image_item(self._client().get_image(image_ref))
        except Exception:
            raise not_found("error.containerImageNotFound", "Image not found")

    def _get_visible_image(self, actor: User, image_ref: str) -> ImageItem:
        image = self._image_by_ref(image_ref)
        if has_permission(actor, CONTAINER_MANAGE_OTHERS):
            return image
        record = self.images.get_for_image(image.id, actor.id)
        if record is None:
            image.is_public = True
            image.source = "docker"
            return image
        image.owner_user_id = record.created_by
        image.is_public = record.is_public
        image.source = record.source
        return image

    def _image_used_by_visible_containers(self, actor: User, image_id: str) -> bool:
        for item in self.list_containers(actor, page=1, page_size=500).items:
            if item.image == image_id or item.image == image_id.replace("sha256:", ""):
                return True
        return False

    def _with_container_usernames(self, items: list[ContainerItem]) -> list[ContainerItem]:
        usernames = self.images.creator_usernames({item.owner_user_id for item in items if item.owner_user_id is not None})
        return [item.model_copy(update={"owner_username": usernames.get(item.owner_user_id, "")}) for item in items]

    def _with_image_usernames(self, items: list[ImageItem]) -> list[ImageItem]:
        usernames = self.images.creator_usernames({item.owner_user_id for item in items if item.owner_user_id is not None})
        return [item.model_copy(update={"owner_username": usernames.get(item.owner_user_id, "")}) for item in items]

    def _validate_container_payload(self, payload: ContainerCreatePayload) -> None:
        if not CONTAINER_NAME_RE.fullmatch(payload.name):
            raise bad_request("error.containerNameInvalid", "Invalid container name")
        for mapping in payload.volumes:
            if mapping.volume_name and not VOLUME_NAME_RE.fullmatch(mapping.volume_name):
                raise bad_request("error.containerVolumeInvalid", "Invalid volume name")
            if not mapping.container_path.startswith("/"):
                raise bad_request("error.containerPathInvalid", "Invalid container path")


def _run_job(job_id: str) -> None:
    with get_session_factory()() as db:
        jobs = ContainerJobRepository(db)
        images = ContainerImageRepository(db)
        job = jobs.get(job_id)
        if job is None:
            return
        job.status = "running"
        job.started_at = utc_now()
        db.commit()
        try:
            client = docker_clients.create_client(_docker_client_config(db))
            if job.kind == "import":
                loaded = client.load_image(Path(job.file_path))
                for image in loaded:
                    item = _image_item(image)
                    images.upsert(item.id, json.dumps(item.repo_tags, ensure_ascii=False), job.created_by, "import")
                    if not job.image_ref:
                        job.image_ref = item.id
            elif job.kind == "export":
                path = Path(job.file_path)
                with path.open("wb") as target:
                    for chunk in client.save_image(job.image_ref):
                        target.write(chunk)
                job.file_size = path.stat().st_size
            else:
                raise DockerOperationError("Unsupported job kind")
            job.status = "success"
            job.finished_at = utc_now()
            db.commit()
        except Exception:
            job.status = "failed"
            job.error_code = "error.containerJobFailed"
            job.finished_at = utc_now()
            db.commit()


def _docker_client_config(db: Session) -> docker_clients.DockerClientConfig:
    settings = SettingService(db).get_settings()
    return docker_clients.DockerClientConfig(mode=settings.docker_connection_mode, host=settings.docker_host)


def _pool() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="container-job")
        return _executor


def _container_item(container) -> ContainerItem:
    attrs = getattr(container, "attrs", {}) or {}
    config = attrs.get("Config", {}) or {}
    network_settings = attrs.get("NetworkSettings", {}) or {}
    ports_data = network_settings.get("Ports", {}) or {}
    image = config.get("Image") or attrs.get("Image") or ""
    return ContainerItem(
        id=str(getattr(container, "id", attrs.get("Id", ""))),
        short_id=str(getattr(container, "short_id", "")) or str(getattr(container, "id", ""))[:12],
        name=_container_name(container),
        image=str(image),
        status=str(getattr(container, "status", attrs.get("State", {}).get("Status", ""))),
        state=str(attrs.get("State", {}).get("Status", getattr(container, "status", ""))),
        ports=_ports(ports_data),
        labels={str(key): str(value) for key, value in (config.get("Labels") or {}).items()},
        created_at=str(attrs.get("Created", "")),
        owner_user_id=_container_owner(container),
    )


def _attach_container_stats(pairs: list[tuple]) -> list[ContainerItem]:
    running = [(raw, item) for raw, item in pairs if item.status == "running" or item.state == "running"]
    stats_by_id: dict[str, tuple[float | None, int | None, int | None]] = {}
    if running:
        with ThreadPoolExecutor(max_workers=min(8, len(running)), thread_name_prefix="container-stats") as pool:
            futures = {pool.submit(_read_container_stats, raw): item.id for raw, item in running}
            for future, container_id in futures.items():
                try:
                    stats_by_id[container_id] = future.result(timeout=5)
                except Exception:
                    stats_by_id[container_id] = (None, None, None)
    items: list[ContainerItem] = []
    for _, item in pairs:
        cpu, mem_used, mem_limit = stats_by_id.get(item.id, (None, None, None))
        items.append(item.model_copy(update={"cpu_percent": cpu, "memory_usage": mem_used, "memory_limit": mem_limit}))
    return items


def _read_container_stats(container) -> tuple[float | None, int | None, int | None]:
    stats = container.stats(stream=False)
    return _parse_container_stats(stats)


def _parse_container_stats(stats: dict) -> tuple[float | None, int | None, int | None]:
    cpu_stats = stats.get("cpu_stats", {}) or {}
    precpu_stats = stats.get("precpu_stats", {}) or {}
    cpu_usage = (cpu_stats.get("cpu_usage", {}) or {}).get("total_usage")
    precpu_usage = (precpu_stats.get("cpu_usage", {}) or {}).get("total_usage")
    system = cpu_stats.get("system_cpu_usage")
    presystem = precpu_stats.get("system_cpu_usage")
    cpu_percent: float | None = None
    if None not in (cpu_usage, precpu_usage, system, presystem):
        cpu_delta = cpu_usage - precpu_usage
        system_delta = system - presystem
        online = cpu_stats.get("online_cpus") or len((cpu_stats.get("cpu_usage", {}) or {}).get("percpu_usage") or []) or 1
        if system_delta > 0 and cpu_delta >= 0:
            cpu_percent = round(cpu_delta / system_delta * online * 100, 2)
    memory_stats = stats.get("memory_stats", {}) or {}
    usage = memory_stats.get("usage")
    limit = memory_stats.get("limit")
    cache = (memory_stats.get("stats", {}) or {}).get("inactive_file")
    if cache is None:
        cache = (memory_stats.get("stats", {}) or {}).get("cache", 0)
    mem_used = max(0, usage - cache) if usage is not None else None
    return cpu_percent, mem_used, limit


def _image_item(image) -> ImageItem:
    attrs = getattr(image, "attrs", {}) or {}
    image_id = str(getattr(image, "id", attrs.get("Id", "")))
    repo_tags = list(getattr(image, "tags", None) or attrs.get("RepoTags") or [])
    return ImageItem(
        id=image_id,
        short_id=str(getattr(image, "short_id", "")) or image_id.replace("sha256:", "")[:12],
        repo_tags=repo_tags,
        size=int(attrs.get("Size", 0) or 0),
        created_at=str(attrs.get("Created", "")),
        labels={str(key): str(value) for key, value in (attrs.get("Config", {}).get("Labels") or {}).items()},
    )


def _container_name(container) -> str:
    return str(getattr(container, "name", "")).lstrip("/")


def _container_owner(container) -> int | None:
    attrs = getattr(container, "attrs", {}) or {}
    labels = (attrs.get("Config", {}) or {}).get("Labels") or {}
    value = labels.get(METRIX_LABEL_OWNER)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ports(ports_data: dict) -> list[str]:
    ports = []
    for private, bindings in ports_data.items():
        if not bindings:
            ports.append(str(private))
            continue
        for binding in bindings:
            host_port = binding.get("HostPort", "")
            ports.append(f"{host_port}->{private}" if host_port else str(private))
    return ports


def _safe_container_name(user_id: int, name: str) -> str:
    return f"metrix-u{user_id}-{name}"


def _safe_environment(env: dict[str, str]) -> dict[str, str]:
    return {key.strip(): value for key, value in env.items() if key.strip() and not SENSITIVE_KEY_RE.search(key)}


def _safe_file_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")


def _imports_dir() -> Path:
    path = PROJECT_DIR / "runtime" / "container_jobs" / "imports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _exports_dir() -> Path:
    path = PROJECT_DIR / "runtime" / "container_jobs" / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path
