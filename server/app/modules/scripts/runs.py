from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import PROJECT_DIR, get_settings
from app.core.exceptions import bad_request, forbidden, not_found
from app.core.time import utc_now
from app.db.session import get_session_factory
from app.models import User
from app.modules.scripts import SCRIPT_MANAGE_OTHERS
from app.modules.scripts import runtime as script_runtime
from app.modules.scripts.models import ScriptProject, ScriptRun, ScriptSchedule
from app.modules.scripts.repositories import ScriptProjectRepository, ScriptRunRepository
from app.modules.scripts.schemas import RunSubmitResponse, ScriptRunItem, ScriptRunListResponse, ScriptRunLog
from app.modules.scripts.services import ScriptProjectService, project_workspace_dir
from app.services.audit import audit_detail, record_audit
from app.services.permissions import has_permission
from app.services.settings import SettingService

SCRIPT_RUN_CLEANUP_INTERVAL_SECONDS = 30 * 60
MAX_LOG_READ_BYTES = 2 * 1024 * 1024
TERMINAL_STATUSES = {"success", "failed", "timeout", "canceled"}
logger = logging.getLogger(__name__)

_executor_lock = threading.Lock()
_executor: ThreadPoolExecutor | None = None
_executor_workers = 0


class ScriptRunService:
    def __init__(self, db: Session):
        self.db = db
        self.projects = ScriptProjectRepository(db)
        self.runs = ScriptRunRepository(db)

    def submit(self, actor: User, project_id: int) -> RunSubmitResponse:
        project = ScriptProjectService(self.db).get_project(actor, project_id)
        run_id = uuid.uuid4().hex
        run = self.runs.create(
            ScriptRun(
                run_id=run_id,
                project_id=project.id,
                trigger="manual",
                status="pending",
                log_path=str(_run_log_path(run_id)),
                created_by=actor.id,
            )
        )
        record_audit(
            self.db,
            actor.id,
            "script.run",
            "script_run",
            run.run_id,
            project.name,
            audit_detail(project.name, meta={"trigger": "manual", "project": project.slug}),
        )
        self.db.commit()
        _pool(self.db).submit(_run_job, run_id)
        return RunSubmitResponse(run_id=run_id, status="pending")

    def list_runs(
        self,
        actor: User,
        project_id: int,
        status: str = "",
        trigger: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> ScriptRunListResponse:
        ScriptProjectService(self.db).get_project(actor, project_id)
        rows, total = self.runs.list(project_id, status, trigger, sort_order, page, page_size)
        usernames = self.runs.creator_usernames({row.created_by for row in rows if row.created_by is not None})
        items = [
            ScriptRunItem.model_validate(row).model_copy(update={"created_by_username": usernames.get(row.created_by, "")})
            for row in rows
        ]
        return ScriptRunListResponse(items=items, total=total, page=page, page_size=page_size)

    def get_run(self, actor: User, run_id: str) -> ScriptRunItem:
        run, _ = self._get_visible_run(actor, run_id)
        username = self.runs.creator_usernames({run.created_by} if run.created_by is not None else set())
        return ScriptRunItem.model_validate(run).model_copy(update={"created_by_username": username.get(run.created_by, "")})

    def run_log(self, actor: User, run_id: str) -> ScriptRunLog:
        run, _ = self._get_visible_run(actor, run_id)
        return ScriptRunLog(run_id=run.run_id, status=run.status, logs=_read_log(run.log_path))

    def cancel(self, actor: User, run_id: str) -> ScriptRunItem:
        run, project = self._get_visible_run(actor, run_id)
        if run.status in TERMINAL_STATUSES:
            raise bad_request("error.scriptRunNotCancelable", "Run cannot be canceled")
        run.status = "canceled"
        run.error_code = "error.scriptRunCanceled"
        run.finished_at = utc_now()
        record_audit(self.db, actor.id, "script.run_cancel", "script_run", run.run_id, project.name)
        self.db.commit()
        script_runtime.remove_run_container(self.db, run_id)
        username = self.runs.creator_usernames({run.created_by} if run.created_by is not None else set())
        return ScriptRunItem.model_validate(run).model_copy(update={"created_by_username": username.get(run.created_by, "")})

    def _get_visible_run(self, actor: User, run_id: str) -> tuple[ScriptRun, ScriptProject]:
        run = self.runs.get(run_id)
        if run is None:
            raise not_found("error.scriptRunNotFound", "Script run not found")
        project = self.projects.get(run.project_id)
        if project is None:
            raise not_found("error.scriptNotFound", "Script project not found")
        if project.created_by == actor.id or has_permission(actor, SCRIPT_MANAGE_OTHERS):
            return run, project
        raise forbidden("error.scriptManageOthersDenied", "You cannot access scripts created by others")


def submit_scheduled_run(project_id: int, schedule_id: int) -> None:
    with get_session_factory()() as db:
        project = ScriptProjectRepository(db).get(project_id)
        if project is None:
            return
        run_id = uuid.uuid4().hex
        ScriptRunRepository(db).create(
            ScriptRun(
                run_id=run_id,
                project_id=project.id,
                trigger="schedule",
                schedule_id=schedule_id,
                status="pending",
                log_path=str(_run_log_path(run_id)),
                created_by=project.created_by,
            )
        )
        schedule = db.get(ScriptSchedule, schedule_id)
        if schedule is not None:
            schedule.last_run_at = utc_now()
        db.commit()
        _pool(db).submit(_run_job, run_id)


def reset_interrupted_runs() -> None:
    try:
        with get_session_factory()() as db:
            now = utc_now()
            rows = db.query(ScriptRun).filter(ScriptRun.status.in_(("pending", "running"))).all()
            for run in rows:
                run.status = "failed"
                run.error_code = "error.scriptRunInterrupted"
                run.finished_at = now
            db.commit()
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
    except SQLAlchemyError as exc:
        logger.warning("Skip interrupted script run reset: %s", exc)


async def script_run_cleanup_loop() -> None:
    while True:
        await asyncio.sleep(SCRIPT_RUN_CLEANUP_INTERVAL_SECONDS)
        await asyncio.to_thread(cleanup_runs_once)


def cleanup_runs_once() -> None:
    try:
        with get_session_factory()() as db:
            hours = SettingService(db).get_settings().script_run_retention_hours
            threshold = utc_now() - timedelta(hours=hours)
            rows = db.query(ScriptRun).filter(ScriptRun.created_at < threshold).all()
            for run in rows:
                _remove_file(run.log_path)
                db.delete(run)
            db.commit()
        _cleanup_orphan_logs()
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
    except SQLAlchemyError as exc:
        logger.warning("Skip script run cleanup: %s", exc)


def shutdown_script_run_executor() -> None:
    global _executor, _executor_workers
    with _executor_lock:
        if _executor is not None:
            _executor.shutdown(wait=True, cancel_futures=False)
        _executor = None
        _executor_workers = 0


def _run_job(run_id: str) -> None:
    with get_session_factory()() as db:
        run = ScriptRunRepository(db).get(run_id)
        if run is None or run.status == "canceled":
            return
        run.status = "running"
        run.started_at = utc_now()
        db.commit()
        project = ScriptProjectRepository(db).get(run.project_id)
        if project is None:
            _finalize(db, run_id, "failed", None, "error.scriptNotFound")
            return
        log_path = Path(run.log_path) if run.log_path else _run_log_path(run_id)
        try:
            adapter = script_runtime.create_adapter(db)
            env = _build_env(db, project)
            workspace = project_workspace_dir(project)
            workspace.mkdir(parents=True, exist_ok=True)
            status, exit_code = script_runtime.run_script(adapter, project, workspace, env, log_path, run_id=run_id)
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {}
            _finalize(db, run_id, "failed", None, str(detail.get("code", "error.scriptRunFailed")))
            return
        except Exception:
            _finalize(db, run_id, "failed", None, "error.scriptRunFailed")
            return
        _finalize(db, run_id, status, exit_code, "")


def _finalize(db: Session, run_id: str, status: str, exit_code: int | None, error_code: str) -> None:
    # Re-read from the database so a cancellation committed by another session is honored
    # instead of the stale "running" status cached in this worker session's identity map.
    db.expire_all()
    run = ScriptRunRepository(db).get(run_id)
    if run is None:
        return
    if run.status == "canceled":
        if run.finished_at is None:
            run.finished_at = utc_now()
            db.commit()
        return
    run.status = status
    run.exit_code = exit_code
    run.error_code = error_code
    run.finished_at = utc_now()
    db.commit()


def _build_env(db: Session, project: ScriptProject) -> dict[str, str]:
    settings = SettingService(db).get_settings()
    env = script_runtime.package_environment(settings)
    env.update(script_runtime.parse_project_env(project.env))
    return env


def _pool(db: Session) -> ThreadPoolExecutor:
    global _executor, _executor_workers
    workers = SettingService(db).get_settings().script_run_max_workers
    with _executor_lock:
        if _executor is None or _executor_workers != workers:
            old = _executor
            _executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="script-run")
            _executor_workers = workers
            if old is not None:
                old.shutdown(wait=True, cancel_futures=False)
        return _executor


def _runs_dir() -> Path:
    runtime_dir = get_settings().runtime_dir
    base = runtime_dir if runtime_dir.is_absolute() else PROJECT_DIR / runtime_dir
    path = base / "script_runs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _run_log_path(run_id: str) -> Path:
    return _runs_dir() / f"{run_id}.log"


def _read_log(log_path: str) -> str:
    if not log_path:
        return ""
    path = Path(log_path)
    if not path.is_file():
        return ""
    data = path.read_bytes()[:MAX_LOG_READ_BYTES]
    return data.decode("utf-8", errors="replace")


def _remove_file(file_path: str) -> None:
    if not file_path:
        return
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError:
        pass


def _cleanup_orphan_logs() -> None:
    try:
        with get_session_factory()() as db:
            known = {run.log_path for run in db.query(ScriptRun.log_path).all() if run.log_path}
    except (HTTPException, SQLAlchemyError):
        return
    for path in _runs_dir().iterdir():
        if path.is_file() and str(path) not in known:
            _remove_file(str(path))
