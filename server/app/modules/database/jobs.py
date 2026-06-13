from __future__ import annotations

import asyncio
import json
import shutil
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from typing import BinaryIO

from fastapi import HTTPException, UploadFile
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import PROJECT_DIR, get_settings
from app.core.exceptions import bad_request, forbidden, not_found
from app.core.security import decrypt_secret
from app.core.time import utc_now
from app.db.session import get_session_factory
from app.models import User
from app.modules.database import DATABASE_MANAGE_OTHERS
from app.modules.database.engines import ExternalDatabase
from app.modules.database.exporters import export_data
from app.modules.database.importers import import_data
from app.modules.database.models import DataJob, DatabaseConnection
from app.modules.database.repositories import DataJobRepository, DatabaseConnectionRepository
from app.modules.database.schemas import (
    DataJobItem,
    DataJobListResponse,
    ExportRequest,
    ImportRequest,
    JobSubmitResponse,
)
from app.modules.database.services import DatabaseService
from app.services.audit import audit_detail, record_audit
from app.services.permissions import has_permission
from app.services.settings import SettingService

DATA_JOB_RETENTION_HOURS = 24
DATA_JOB_CLEANUP_INTERVAL_SECONDS = 30 * 60

_executor_lock = threading.Lock()
_executor: ThreadPoolExecutor | None = None
_executor_workers = 0


class DataJobService:
    def __init__(self, db: Session):
        self.db = db
        self.connections = DatabaseConnectionRepository(db)
        self.jobs = DataJobRepository(db)

    def submit_export(self, actor: User, conn_id: str, payload: ExportRequest) -> JobSubmitResponse:
        connection = DatabaseService(self.db)._get_usable(actor, conn_id)
        job_id = uuid.uuid4().hex
        path = _exports_dir() / f"{job_id}.{payload.format}"
        params = payload.model_dump()
        params["format"] = payload.format
        job = self.jobs.create(
            DataJob(
                job_id=job_id,
                kind="export",
                connection_id=connection.id,
                format=payload.format,
                params_json=json.dumps(params, ensure_ascii=False),
                status="pending",
                file_name=f"{connection.conn_id}-{job_id}.{payload.format}",
                file_path=str(path),
                created_by=actor.id,
            )
        )
        record_audit(
            self.db,
            actor.id,
            "database.export_submit",
            "data_job",
            job.job_id,
            job.file_name,
            audit_detail(job.file_name, meta={"conn_id": connection.conn_id, "format": payload.format}),
        )
        self.db.commit()
        _pool(self.db).submit(_run_job, job_id)
        return JobSubmitResponse(job_id=job_id, status="pending")

    def submit_import(self, actor: User, conn_id: str, payload: ImportRequest, file: UploadFile) -> JobSubmitResponse:
        connection = DatabaseService(self.db)._get_usable(actor, conn_id)
        job_id = uuid.uuid4().hex
        suffix = Path(file.filename or f"import.{payload.format}").suffix or f".{payload.format}"
        path = _imports_dir() / f"{job_id}{suffix}"
        with path.open("wb") as target:
            shutil.copyfileobj(file.file, target)
        params = payload.model_dump()
        params["format"] = payload.format
        job = self.jobs.create(
            DataJob(
                job_id=job_id,
                kind="import",
                connection_id=connection.id,
                format=payload.format,
                params_json=json.dumps(params, ensure_ascii=False),
                status="pending",
                file_name=file.filename or path.name,
                file_path=str(path),
                created_by=actor.id,
            )
        )
        record_audit(
            self.db,
            actor.id,
            "database.import_submit",
            "data_job",
            job.job_id,
            job.file_name,
            audit_detail(job.file_name, meta={"conn_id": connection.conn_id, "format": payload.format}),
        )
        self.db.commit()
        _pool(self.db).submit(_run_job, job_id)
        return JobSubmitResponse(job_id=job_id, status="pending")

    def list_jobs(self, actor: User, kind: str = "", status: str = "", page: int = 1, page_size: int = 20) -> DataJobListResponse:
        visible_to = None if has_permission(actor, DATABASE_MANAGE_OTHERS) else actor.id
        rows, total = self.jobs.list(kind, status, visible_to, page, page_size)
        return DataJobListResponse(items=[self._item(row) for row in rows], total=total, page=page, page_size=page_size)

    def get_job(self, actor: User, job_id: str) -> DataJobItem:
        job = self._get_visible(actor, job_id)
        return self._item(job)

    def download(self, actor: User, job_id: str) -> tuple[str, BinaryIO]:
        job = self._get_visible(actor, job_id)
        if job.kind != "export" or job.status != "success":
            raise bad_request("error.dataJobNotDownloadable", "Data job is not downloadable")
        path = Path(job.file_path)
        if not path.is_file():
            raise not_found("error.dataJobFileMissing", "Data job file missing")
        fileobj = path.open("rb")
        record_audit(
            self.db,
            actor.id,
            "database.export_download",
            "data_job",
            job.job_id,
            job.file_name,
            audit_detail(job.file_name, meta={"format": job.format, "file_size": job.file_size}),
        )
        self.db.commit()
        return job.file_name, _download_stream(job.job_id, fileobj)

    def delete(self, actor: User, job_id: str) -> None:
        job = self._get_visible(actor, job_id)
        _remove_file(job.file_path)
        self.jobs.delete(job)
        self.db.commit()

    def _get_visible(self, actor: User, job_id: str) -> DataJob:
        job = self.jobs.get(job_id)
        if job is None:
            raise not_found()
        if job.created_by == actor.id or has_permission(actor, DATABASE_MANAGE_OTHERS):
            return job
        raise forbidden()

    def _item(self, job: DataJob) -> DataJobItem:
        connection = self.connections.get(job.connection_id)
        return DataJobItem.model_validate(job).model_copy(
            update={
                "conn_id": connection.conn_id if connection else "",
                "connection_name": connection.name if connection else "",
            }
        )


def reset_interrupted_jobs() -> None:
    try:
        with get_session_factory()() as db:
            now = utc_now()
            rows = db.query(DataJob).filter(DataJob.status.in_(("pending", "running"))).all()
            for job in rows:
                job.status = "failed"
                job.error_code = "error.dataJobInterrupted"
                job.finished_at = now
            db.commit()
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
    except SQLAlchemyError:
        return


async def data_job_cleanup_loop() -> None:
    while True:
        await asyncio.sleep(DATA_JOB_CLEANUP_INTERVAL_SECONDS)
        await asyncio.to_thread(cleanup_data_jobs_once)


def cleanup_data_jobs_once() -> None:
    try:
        with get_session_factory()() as db:
            now = utc_now()
            rows = (
                db.query(DataJob)
                .filter((DataJob.expires_at.is_not(None) & (DataJob.expires_at < now)) | DataJob.downloaded_at.is_not(None))
                .all()
            )
            for job in rows:
                _remove_file(job.file_path)
                db.delete(job)
            db.commit()
        _cleanup_orphan_files()
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
    except SQLAlchemyError:
        return


def shutdown_data_job_executor() -> None:
    global _executor, _executor_workers
    with _executor_lock:
        if _executor is not None:
            _executor.shutdown(wait=False)
        _executor = None
        _executor_workers = 0


def _run_job(job_id: str) -> None:
    with get_session_factory()() as db:
        job = db.query(DataJob).filter(DataJob.job_id == job_id).first()
        if job is None:
            return
        job.status = "running"
        job.started_at = utc_now()
        db.commit()
        connection = db.get(DatabaseConnection, job.connection_id)
        if connection is None:
            _fail_job(db, job, "error.databaseConnectionMissing")
            return
        params = json.loads(job.params_json or "{}")
        try:
            password = decrypt_secret(connection.password_encrypted)
            with ExternalDatabase(connection, password, str(params.get("database") or "")) as runtime:
                if job.kind == "export":
                    _ensure_parent(job.file_path)
                    row_count = export_data(runtime, params, Path(job.file_path))
                    job.file_size = Path(job.file_path).stat().st_size if Path(job.file_path).is_file() else 0
                    job.expires_at = utc_now() + timedelta(hours=DATA_JOB_RETENTION_HOURS)
                else:
                    row_count = import_data(runtime, params, Path(job.file_path))
                    _remove_file(job.file_path)
                    job.file_path = ""
                    job.expires_at = None
                job.row_count = row_count
                job.status = "success"
                job.finished_at = utc_now()
                db.commit()
        except BaseException as exc:
            if job.kind == "import":
                _remove_file(job.file_path)
            _fail_job(db, job, str(exc)[:120] or "error.dataJobFailed")


def _fail_job(db: Session, job: DataJob, error_code: str) -> None:
    job.status = "failed"
    job.error_code = error_code
    job.finished_at = utc_now()
    db.commit()


def _pool(db: Session) -> ThreadPoolExecutor:
    global _executor, _executor_workers
    workers = SettingService(db).get_settings().data_job_max_workers
    with _executor_lock:
        if _executor is None or _executor_workers != workers:
            old = _executor
            _executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="data-job")
            _executor_workers = workers
            if old is not None:
                old.shutdown(wait=False)
        return _executor


def _download_stream(job_id: str, fileobj: BinaryIO):
    try:
        while True:
            chunk = fileobj.read(1024 * 1024)
            if not chunk:
                break
            yield chunk
    finally:
        fileobj.close()
        with get_session_factory()() as db:
            job = db.query(DataJob).filter(DataJob.job_id == job_id).first()
            if job is not None:
                _remove_file(job.file_path)
                job.downloaded_at = utc_now()
                db.commit()


def _runtime_dir() -> Path:
    runtime = get_settings().runtime_dir
    return runtime if runtime.is_absolute() else PROJECT_DIR / runtime


def _exports_dir() -> Path:
    path = _runtime_dir() / "exports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _imports_dir() -> Path:
    path = _runtime_dir() / "imports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ensure_parent(file_path: str) -> None:
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


def _remove_file(file_path: str) -> None:
    if not file_path:
        return
    try:
        Path(file_path).unlink(missing_ok=True)
    except OSError:
        pass


def _cleanup_orphan_files() -> None:
    for directory in (_exports_dir(), _imports_dir()):
        for path in directory.iterdir():
            if path.is_file() and path.stat().st_mtime < (utc_now() - timedelta(hours=DATA_JOB_RETENTION_HOURS)).timestamp():
                _remove_file(str(path))
