from __future__ import annotations

import json
import posixpath
import secrets
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.config import PROJECT_DIR, get_settings
from app.core.exceptions import bad_request, forbidden, not_found
from app.models import User
from app.modules.scripts import SCRIPT_MANAGE_OTHERS
from app.modules.scripts.models import ScriptProject, ScriptRun, ScriptSchedule
from app.modules.scripts.repositories import ScriptProjectRepository
from app.modules.scripts.schemas import (
    ScriptFileContent,
    ScriptFileEntry,
    ScriptFileListResponse,
    ScriptProjectItem,
    ScriptProjectListResponse,
    ScriptProjectPayload,
)
from app.services.audit import audit_changes, audit_detail, record_audit
from app.services.permissions import has_permission
from app.services.settings import SettingService

SLUG_PREFIX = "scr_"
MAX_READ_BYTES = 2 * 1024 * 1024
ENTRY_NAME_INVALID_CHARS = ("/", "\\", "\0")
ARCHIVE_SUFFIXES = (".zip", ".rar", ".7z")


class ScriptProjectService:
    def __init__(self, db: Session):
        self.db = db
        self.projects = ScriptProjectRepository(db)

    def list_projects(
        self,
        actor: User,
        keyword: str = "",
        language: str = "",
        network_mode: str = "",
        created_by: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> ScriptProjectListResponse:
        visible_to = None if has_permission(actor, SCRIPT_MANAGE_OTHERS) else actor.id
        created_by_user_id = actor.id if created_by == "me" else None
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        rows, total = self.projects.list(
            keyword,
            language,
            network_mode,
            created_by_user_id,
            visible_to,
            created_at_order,
            page,
            page_size,
        )
        return ScriptProjectListResponse(
            items=self._with_creator_usernames(rows),
            total=total,
            page=page,
            page_size=page_size,
        )

    def create(self, actor: User, payload: ScriptProjectPayload) -> ScriptProjectItem:
        project = self.projects.create(
            ScriptProject(
                slug=self._generate_slug(),
                name=payload.name,
                description=payload.description,
                language=payload.language,
                base_image=payload.base_image,
                network_mode=payload.network_mode,
                is_shared=payload.is_shared,
                run_command=payload.run_command,
                env=json.dumps(payload.env, ensure_ascii=False),
                cpu_limit=payload.cpu_limit,
                memory_limit_mb=payload.memory_limit_mb,
                timeout_seconds=payload.timeout_seconds,
                created_by=actor.id,
            )
        )
        project.workspace_path = _relative_workspace(project)
        _project_workspace_dir(project).mkdir(parents=True, exist_ok=True)
        record_audit(
            self.db,
            actor.id,
            "script.create",
            "script_project",
            project.slug,
            project.name,
            audit_detail(project.name, meta=_project_snapshot(project)),
        )
        self.db.commit()
        return self._with_creator_username(project, actor.username)

    def update(self, actor: User, project_id: int, payload: ScriptProjectPayload) -> ScriptProjectItem:
        project = self._get(project_id)
        self._ensure_can_manage(actor, project)
        before = _project_snapshot(project)
        project.name = payload.name
        project.description = payload.description
        project.language = payload.language
        project.base_image = payload.base_image
        project.network_mode = payload.network_mode
        project.is_shared = payload.is_shared
        project.run_command = payload.run_command
        project.env = json.dumps(payload.env, ensure_ascii=False)
        project.cpu_limit = payload.cpu_limit
        project.memory_limit_mb = payload.memory_limit_mb
        project.timeout_seconds = payload.timeout_seconds
        record_audit(
            self.db,
            actor.id,
            "script.update",
            "script_project",
            project.slug,
            project.name,
            audit_detail(project.name, audit_changes(before, _project_snapshot(project))),
        )
        self.db.commit()
        creator_name = actor.username if project.created_by == actor.id else self._creator_username(project)
        return self._with_creator_username(project, creator_name)

    def delete(self, actor: User, project_id: int) -> None:
        project = self._get(project_id)
        self._ensure_can_manage(actor, project)
        from app.modules.scripts import runtime as script_runtime
        from app.modules.scripts import scheduler as script_scheduler

        for schedule in self.db.query(ScriptSchedule).filter(ScriptSchedule.project_id == project.id).all():
            script_scheduler.unregister_schedule(schedule.id)
            self.db.delete(schedule)
        self.db.query(ScriptRun).filter(ScriptRun.project_id == project.id).delete(synchronize_session=False)
        workspace = _project_workspace_dir(project)
        record_audit(
            self.db,
            actor.id,
            "script.delete",
            "script_project",
            project.slug,
            project.name,
            audit_detail(project.name, meta=_project_snapshot(project)),
        )
        project_id_value = project.id
        self.projects.delete(project)
        self.db.commit()
        script_runtime.remove_project_containers(self.db, project_id_value)
        shutil.rmtree(workspace, ignore_errors=True)

    def get_project(self, actor: User, project_id: int) -> ScriptProject:
        # Read/run access: creator, any shared project, or managers of others' scripts.
        project = self._get(project_id)
        if project.created_by == actor.id or project.is_shared or has_permission(actor, SCRIPT_MANAGE_OTHERS):
            return project
        raise forbidden("error.scriptManageOthersDenied", "You cannot access scripts created by others")

    def get_manageable_project(self, actor: User, project_id: int) -> ScriptProject:
        # Edit access (config, files, terminal, schedules): creator or admin only.
        # Sharing only grants read + run, never edit, even for users who can see the project.
        project = self._get(project_id)
        self._ensure_can_manage(actor, project)
        return project

    def project_item(self, project: ScriptProject) -> ScriptProjectItem:
        return self._with_creator_username(project, self._creator_username(project))

    # --- workspace files -------------------------------------------------

    def list_files(self, actor: User, project_id: int, path: str = "/") -> ScriptFileListResponse:
        project = self.get_project(actor, project_id)
        root = _ensure_workspace(project)
        target = _safe_target(root, path)
        if not target.exists():
            raise not_found("error.scriptPathNotFound", "Path not found")
        if not target.is_dir():
            raise bad_request("error.scriptNotDirectory", "Target is not a directory")
        entries = [
            _entry(root, child)
            for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        ]
        return ScriptFileListResponse(path=_virtual_path(path), entries=entries)

    def read_file(self, actor: User, project_id: int, path: str) -> ScriptFileContent:
        project = self.get_project(actor, project_id)
        root = _ensure_workspace(project)
        target = _safe_target(root, path)
        if not target.is_file():
            raise not_found("error.scriptPathNotFound", "File not found")
        data = target.read_bytes()
        truncated = len(data) > MAX_READ_BYTES
        content = data[:MAX_READ_BYTES].decode("utf-8", errors="replace")
        return ScriptFileContent(path=_virtual_path(path), content=content, truncated=truncated)

    def write_file(self, actor: User, project_id: int, path: str, content: str) -> ScriptFileEntry:
        project = self.get_manageable_project(actor, project_id)
        root = _ensure_workspace(project)
        target = _safe_target(root, path)
        if target == root.resolve():
            raise bad_request("error.scriptPathInvalid", "Invalid path")
        data = content.encode("utf-8")
        existing = target.stat().st_size if target.is_file() else 0
        self._ensure_quota(root, len(data) - existing)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        record_audit(self.db, actor.id, "script.file_write", "script_project", project.slug, _virtual_path(path))
        self.db.commit()
        return _entry(root, target)

    def upload_file(
        self,
        actor: User,
        project_id: int,
        path: str,
        filename: str,
        fileobj: BinaryIO,
        size: int | None,
    ) -> ScriptFileEntry:
        project = self.get_manageable_project(actor, project_id)
        root = _ensure_workspace(project)
        directory = _safe_target(root, path)
        if not directory.is_dir():
            raise bad_request("error.scriptNotDirectory", "Target is not a directory")
        name = _validated_name(posixpath.basename(filename.replace("\\", "/")))
        data = fileobj.read()
        if _is_archive(name):
            # ZIP/RAR/7Z uploads are auto-extracted into the target directory.
            entry = self._extract_archive(root, _virtual_path(path), data, name)
            record_audit(self.db, actor.id, "script.archive_extract", "script_project", project.slug, entry.path)
            self.db.commit()
            return entry
        target = _safe_target(root, posixpath.join(_virtual_path(path), name))
        existing = target.stat().st_size if target.is_file() else 0
        self._ensure_quota(root, len(data) - existing)
        target.write_bytes(data)
        entry = _entry(root, target)
        record_audit(self.db, actor.id, "script.file_upload", "script_project", project.slug, entry.path)
        self.db.commit()
        return entry

    def mkdir(self, actor: User, project_id: int, path: str) -> ScriptFileEntry:
        project = self.get_manageable_project(actor, project_id)
        root = _ensure_workspace(project)
        target = _safe_target(root, path)
        if target == root.resolve():
            raise bad_request("error.scriptPathInvalid", "Invalid path")
        if target.exists():
            raise bad_request("error.scriptEntryExists", "Entry already exists")
        target.mkdir(parents=True, exist_ok=True)
        record_audit(self.db, actor.id, "script.file_mkdir", "script_project", project.slug, _virtual_path(path))
        self.db.commit()
        return _entry(root, target)

    def rename(self, actor: User, project_id: int, path: str, new_name: str) -> ScriptFileEntry:
        project = self.get_manageable_project(actor, project_id)
        root = _ensure_workspace(project)
        target = _safe_target(root, path)
        if target == root.resolve() or not target.exists():
            raise bad_request("error.scriptPathInvalid", "Invalid path")
        name = _validated_name(new_name)
        destination = _safe_target(root, posixpath.join(posixpath.dirname(_virtual_path(path)), name))
        if destination.exists():
            raise bad_request("error.scriptEntryExists", "Entry already exists")
        target.rename(destination)
        entry = _entry(root, destination)
        record_audit(self.db, actor.id, "script.file_rename", "script_project", project.slug, entry.path)
        self.db.commit()
        return entry

    def delete_entry(self, actor: User, project_id: int, path: str) -> None:
        project = self.get_manageable_project(actor, project_id)
        root = _ensure_workspace(project)
        target = _safe_target(root, path)
        if target == root.resolve() or not target.exists():
            raise bad_request("error.scriptPathInvalid", "Invalid path")
        if target.is_dir():
            shutil.rmtree(target, ignore_errors=True)
        else:
            target.unlink(missing_ok=True)
        record_audit(self.db, actor.id, "script.file_delete", "script_project", project.slug, _virtual_path(path))
        self.db.commit()

    # --- helpers ---------------------------------------------------------

    def _ensure_quota(self, root: Path, delta_bytes: int) -> None:
        if delta_bytes <= 0:
            return
        quota_mb = SettingService(self.db).get_settings().script_workspace_quota_mb
        limit = quota_mb * 1024 * 1024
        if _directory_size(root) + delta_bytes > limit:
            raise bad_request("error.scriptQuotaExceeded", "Workspace quota exceeded", quota_mb=quota_mb)

    def _extract_archive(self, root: Path, virtual_dir: str, data: bytes, name: str) -> ScriptFileEntry:
        # Extract into an isolated temp dir first, then copy each regular file into the
        # workspace through _safe_target so archive members can never escape the root.
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "upload.archive"
            archive_path.write_bytes(data)
            staging = Path(tmp) / "out"
            staging.mkdir()
            _extract_to(name, archive_path, staging)
            self._ensure_quota(root, _directory_size(staging))
            for item in sorted(staging.rglob("*")):
                if item.is_dir():
                    continue
                relative = item.relative_to(staging).as_posix()
                dest = _safe_target(root, posixpath.join(virtual_dir, relative))
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item, dest)
        return _entry(root, _safe_target(root, virtual_dir))

    def _get(self, project_id: int) -> ScriptProject:
        project = self.projects.get(project_id)
        if project is None:
            raise not_found("error.scriptNotFound", "Script project not found")
        return project

    def _ensure_can_manage(self, actor: User, project: ScriptProject) -> None:
        if project.created_by == actor.id or has_permission(actor, SCRIPT_MANAGE_OTHERS):
            return
        raise forbidden("error.scriptManageOthersDenied", "You cannot manage scripts created by others")

    def _generate_slug(self) -> str:
        while True:
            candidate = f"{SLUG_PREFIX}{secrets.token_hex(5)}"
            if self.projects.get_by_slug(candidate) is None:
                return candidate

    def _with_creator_usernames(self, projects: list[ScriptProject]) -> list[ScriptProjectItem]:
        user_ids = {project.created_by for project in projects if project.created_by is not None}
        usernames = self.projects.creator_usernames(user_ids)
        return [self._with_creator_username(project, usernames.get(project.created_by, "")) for project in projects]

    def _with_creator_username(self, project: ScriptProject, username: str) -> ScriptProjectItem:
        return ScriptProjectItem(
            id=project.id,
            slug=project.slug,
            name=project.name,
            description=project.description,
            language=project.language,
            base_image=project.base_image,
            network_mode=project.network_mode,
            is_shared=project.is_shared,
            run_command=project.run_command,
            env=_parse_env(project.env),
            cpu_limit=project.cpu_limit,
            memory_limit_mb=project.memory_limit_mb,
            timeout_seconds=project.timeout_seconds,
            workspace_path=project.workspace_path,
            created_by=project.created_by,
            created_by_username=username,
            created_at=project.created_at,
            updated_at=project.updated_at,
        )

    def _creator_username(self, project: ScriptProject) -> str:
        if project.created_by is None:
            return ""
        return self.projects.creator_usernames({project.created_by}).get(project.created_by, "")


def scripts_root() -> Path:
    runtime = get_settings().runtime_dir
    base = runtime if runtime.is_absolute() else PROJECT_DIR / runtime
    return base / "script_workspaces"


def project_workspace_dir(project: ScriptProject) -> Path:
    return _project_workspace_dir(project)


def _project_workspace_dir(project: ScriptProject) -> Path:
    return scripts_root() / f"u{project.created_by or 0}" / f"p{project.id}"


def _relative_workspace(project: ScriptProject) -> str:
    return f"script_workspaces/u{project.created_by or 0}/p{project.id}"


def _ensure_workspace(project: ScriptProject) -> Path:
    workspace = _project_workspace_dir(project)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _virtual_path(path: str) -> str:
    cleaned = (path or "/").replace("\\", "/")
    depth = 0
    for segment in cleaned.split("/"):
        if segment in ("", "."):
            continue
        depth = depth - 1 if segment == ".." else depth + 1
        if depth < 0:
            raise bad_request("error.scriptPathInvalid", "Invalid path")
    normalized = posixpath.normpath("/" + cleaned.strip("/"))
    return "/" if normalized == "/" else normalized


def _safe_target(root: Path, path: str) -> Path:
    virtual = _virtual_path(path)
    target = (root / virtual.lstrip("/")).resolve()
    root_resolved = root.resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise bad_request("error.scriptPathInvalid", "Invalid path")
    return target


def _is_archive(name: str) -> bool:
    return name.lower().endswith(ARCHIVE_SUFFIXES)


def _extract_to(name: str, archive_path: Path, dest_dir: Path) -> None:
    lower = name.lower()
    if lower.endswith(".zip"):
        try:
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(dest_dir)
        except zipfile.BadZipFile:
            raise bad_request("error.scriptArchiveInvalid", "Invalid archive", fmt="zip")
        return
    if lower.endswith(".7z"):
        try:
            import py7zr
        except ImportError:
            raise bad_request("error.scriptArchiveToolMissing", "7z support is not installed", fmt="7z")
        try:
            with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                archive.extractall(path=dest_dir)
        except Exception:
            raise bad_request("error.scriptArchiveInvalid", "Invalid archive", fmt="7z")
        return
    if lower.endswith(".rar"):
        try:
            import rarfile
        except ImportError:
            raise bad_request("error.scriptArchiveToolMissing", "rar support is not installed", fmt="rar")
        try:
            with rarfile.RarFile(archive_path) as archive:
                archive.extractall(dest_dir)
        except rarfile.RarCannotExec:
            raise bad_request("error.scriptArchiveToolMissing", "An unrar/7z tool is required on the server", fmt="rar")
        except Exception:
            raise bad_request("error.scriptArchiveInvalid", "Invalid archive", fmt="rar")
        return
    raise bad_request("error.scriptArchiveInvalid", "Unsupported archive", fmt=name)


def _validated_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or cleaned in (".", "..") or any(char in cleaned for char in ENTRY_NAME_INVALID_CHARS) or len(cleaned) > 255:
        raise bad_request("error.scriptNameInvalid", "Invalid file or directory name")
    return cleaned


def _entry(root: Path, target: Path) -> ScriptFileEntry:
    relative = target.resolve().relative_to(root.resolve()).as_posix()
    is_dir = target.is_dir()
    return ScriptFileEntry(
        name=target.name,
        path="/" + relative if relative != "." else "/",
        is_dir=is_dir,
        size=0 if is_dir else target.stat().st_size,
        modified_at=_modified_at(target),
    )


def _modified_at(target: Path) -> str:
    try:
        return datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return ""


def _directory_size(root: Path) -> int:
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                total += path.stat().st_size
            except OSError:
                continue
    return total


def _parse_env(value: str) -> dict[str, str]:
    try:
        data = json.loads(value or "{}")
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(item) for key, item in data.items()}


def _project_snapshot(project: ScriptProject) -> dict[str, object]:
    return {
        "slug": project.slug,
        "name": project.name,
        "language": project.language,
        "base_image": project.base_image,
        "network_mode": project.network_mode,
        "is_shared": project.is_shared,
        "run_command": project.run_command,
        "cpu_limit": project.cpu_limit,
        "memory_limit_mb": project.memory_limit_mb,
        "timeout_seconds": project.timeout_seconds,
    }
