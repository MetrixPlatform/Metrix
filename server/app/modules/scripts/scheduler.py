from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found
from app.db.session import get_session_factory
from app.models import User
from app.modules.scripts import SCRIPT_MANAGE_OTHERS
from app.modules.scripts.models import ScriptProject, ScriptSchedule
from app.modules.scripts.repositories import ScriptProjectRepository, ScriptScheduleRepository
from app.modules.scripts.runs import submit_scheduled_run
from app.modules.scripts.schemas import ScriptSchedulePayload, ScriptScheduleItem
from app.modules.scripts.services import ScriptProjectService
from app.services.audit import audit_detail, record_audit
from app.services.permissions import has_permission

logger = logging.getLogger(__name__)

_scheduler_lock = threading.Lock()
_scheduler: BackgroundScheduler | None = None


class ScriptScheduleService:
    def __init__(self, db: Session):
        self.db = db
        self.schedules = ScriptScheduleRepository(db)
        self.projects = ScriptProjectRepository(db)

    def list_schedules(self, actor: User, project_id: int) -> list[ScriptScheduleItem]:
        ScriptProjectService(self.db).get_project(actor, project_id)
        return [ScriptScheduleItem.model_validate(row) for row in self.schedules.list_for_project(project_id)]

    def create(self, actor: User, project_id: int, payload: ScriptSchedulePayload) -> ScriptScheduleItem:
        project = ScriptProjectService(self.db).get_manageable_project(actor, project_id)
        _validate_payload(payload)
        schedule = self.schedules.create(
            ScriptSchedule(
                project_id=project.id,
                name=payload.name,
                trigger_type=payload.trigger_type,
                interval_seconds=payload.interval_seconds,
                cron_expr=payload.cron_expr,
                enabled=payload.enabled,
                created_by=actor.id,
            )
        )
        self._apply(schedule)
        record_audit(
            self.db,
            actor.id,
            "script.schedule_create",
            "script_schedule",
            str(schedule.id),
            project.name,
            audit_detail(project.name, meta=_schedule_snapshot(schedule)),
        )
        self.db.commit()
        return ScriptScheduleItem.model_validate(schedule)

    def update(self, actor: User, schedule_id: int, payload: ScriptSchedulePayload) -> ScriptScheduleItem:
        schedule, project = self._get_visible(actor, schedule_id)
        _validate_payload(payload)
        schedule.name = payload.name
        schedule.trigger_type = payload.trigger_type
        schedule.interval_seconds = payload.interval_seconds
        schedule.cron_expr = payload.cron_expr
        schedule.enabled = payload.enabled
        self._apply(schedule)
        record_audit(
            self.db,
            actor.id,
            "script.schedule_update",
            "script_schedule",
            str(schedule.id),
            project.name,
            audit_detail(project.name, meta=_schedule_snapshot(schedule)),
        )
        self.db.commit()
        return ScriptScheduleItem.model_validate(schedule)

    def delete(self, actor: User, schedule_id: int) -> None:
        schedule, project = self._get_visible(actor, schedule_id)
        unregister_schedule(schedule.id)
        record_audit(
            self.db,
            actor.id,
            "script.schedule_delete",
            "script_schedule",
            str(schedule.id),
            project.name,
            audit_detail(project.name, meta=_schedule_snapshot(schedule)),
        )
        self.schedules.delete(schedule)
        self.db.commit()

    def _apply(self, schedule: ScriptSchedule) -> None:
        if schedule.enabled:
            schedule.next_run_at = register_schedule(schedule)
        else:
            unregister_schedule(schedule.id)
            schedule.next_run_at = None

    def _get_visible(self, actor: User, schedule_id: int) -> tuple[ScriptSchedule, ScriptProject]:
        schedule = self.schedules.get(schedule_id)
        if schedule is None:
            raise not_found("error.scriptScheduleNotFound", "Schedule not found")
        project = self.projects.get(schedule.project_id)
        if project is None:
            raise not_found("error.scriptNotFound", "Script project not found")
        if project.created_by == actor.id or has_permission(actor, SCRIPT_MANAGE_OTHERS):
            return schedule, project
        raise forbidden("error.scriptManageOthersDenied", "You cannot manage scripts created by others")


def start_scheduler() -> None:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None:
            return
        scheduler = BackgroundScheduler()
        scheduler.start()
        _scheduler = scheduler
    _reload_schedules()


def shutdown_scheduler() -> None:
    global _scheduler
    with _scheduler_lock:
        scheduler = _scheduler
        _scheduler = None
    if scheduler is not None:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass


def register_schedule(schedule: ScriptSchedule) -> datetime | None:
    trigger = _build_trigger(schedule)
    with _scheduler_lock:
        scheduler = _scheduler
    if scheduler is not None:
        job = scheduler.add_job(
            submit_scheduled_run,
            trigger=trigger,
            args=[schedule.project_id, schedule.id],
            id=_job_id(schedule.id),
            replace_existing=True,
            max_instances=1,
            coalesce=True,
        )
        return _to_utc(job.next_run_time)
    return _compute_next_run(trigger)


def unregister_schedule(schedule_id: int) -> None:
    with _scheduler_lock:
        scheduler = _scheduler
    if scheduler is None:
        return
    try:
        scheduler.remove_job(_job_id(schedule_id))
    except Exception:
        pass


def _reload_schedules() -> None:
    try:
        with get_session_factory()() as db:
            for schedule in ScriptScheduleRepository(db).list_enabled():
                try:
                    schedule.next_run_at = register_schedule(schedule)
                except HTTPException:
                    continue
            db.commit()
    except (HTTPException, SQLAlchemyError) as exc:
        logger.warning("Skip script schedule reload: %s", exc)


def _validate_payload(payload: ScriptSchedulePayload) -> None:
    if payload.trigger_type == "interval":
        if not payload.interval_seconds:
            raise bad_request("error.scriptScheduleInvalid", "Interval seconds required")
        return
    try:
        CronTrigger.from_crontab(payload.cron_expr)
    except (ValueError, KeyError):
        raise bad_request("error.scriptCronInvalid", "Invalid cron expression")


def _build_trigger(schedule: ScriptSchedule):
    if schedule.trigger_type == "interval":
        if not schedule.interval_seconds:
            raise bad_request("error.scriptScheduleInvalid", "Interval seconds required")
        return IntervalTrigger(seconds=schedule.interval_seconds)
    try:
        return CronTrigger.from_crontab(schedule.cron_expr)
    except (ValueError, KeyError):
        raise bad_request("error.scriptCronInvalid", "Invalid cron expression")


def _compute_next_run(trigger) -> datetime | None:
    try:
        nxt = trigger.get_next_fire_time(None, datetime.now(timezone.utc))
    except Exception:
        return None
    return _to_utc(nxt)


def _to_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc)


def _job_id(schedule_id: int) -> str:
    return f"script-schedule-{schedule_id}"


def _schedule_snapshot(schedule: ScriptSchedule) -> dict[str, object]:
    return {
        "name": schedule.name,
        "trigger_type": schedule.trigger_type,
        "interval_seconds": schedule.interval_seconds,
        "cron_expr": schedule.cron_expr,
        "enabled": schedule.enabled,
    }
