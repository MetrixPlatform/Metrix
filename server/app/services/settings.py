from __future__ import annotations

import json
import re
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.install import load_install_config
from app.models import AuditLog, User
from app.repositories.settings import SystemSettingRepository
from app.schemas.settings import PublicSettings, RegistrationRequiredFields, SystemSettings, SystemSettingsUpdate
from app.services.audit import audit_changes, audit_detail, record_audit
from app.services.data_portability import export_database, list_database_tables

SETTING_APP_NAME = "app_name"
SETTING_REGISTRATION_ENABLED = "registration_enabled"
SETTING_REGISTRATION_APPROVAL_REQUIRED = "registration_approval_required"
SETTING_REQUIRED_FIELDS = "registration_required_fields"
SETTING_LOG_RETENTION_DAYS = "log_retention_days"
SETTING_DEFAULT_LOCALE = "default_locale"
SETTING_API_ENABLED = "api_enabled"
SETTING_API_TOKEN_REVEAL_ENABLED = "api_token_reveal_enabled"
SETTING_DATA_JOB_MAX_WORKERS = "data_job_max_workers"
SETTING_DATA_JOB_RETENTION_DAYS = "data_job_retention_days"
SETTING_NAVIGATION_ORDER = "navigation_order"
DEFAULT_LOG_RETENTION_DAYS = 90
DEFAULT_DATA_JOB_MAX_WORKERS = 2
DEFAULT_DATA_JOB_RETENTION_DAYS = 7
NAVIGATION_KEY_RE = re.compile(r"^(path:/[a-zA-Z0-9_./-]*|group:[a-zA-Z0-9_-]+)$")


class SettingService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = SystemSettingRepository(db)

    def public_settings(self) -> PublicSettings:
        data = self._merged_settings()
        return PublicSettings(
            app_name=data.app_name,
            registration_enabled=data.registration_enabled,
            registration_approval_required=data.registration_approval_required,
            registration_required_fields=data.registration_required_fields,
            default_locale=data.default_locale,
            api_enabled=data.api_enabled,
            api_token_reveal_enabled=data.api_token_reveal_enabled,
            navigation_order=data.navigation_order,
        )

    def get_settings(self) -> SystemSettings:
        return self._merged_settings()

    def update_settings(self, actor: User, payload: SystemSettingsUpdate) -> SystemSettings:
        before = _settings_snapshot(self.get_settings())
        self.settings.set_many(
            {
                SETTING_APP_NAME: payload.app_name.strip(),
                SETTING_REGISTRATION_ENABLED: _dump_bool(payload.registration_enabled),
                SETTING_REGISTRATION_APPROVAL_REQUIRED: _dump_bool(payload.registration_approval_required),
                SETTING_REQUIRED_FIELDS: payload.registration_required_fields.model_dump_json(),
                SETTING_LOG_RETENTION_DAYS: str(payload.log_retention_days),
                SETTING_DEFAULT_LOCALE: payload.default_locale,
                SETTING_API_ENABLED: _dump_bool(payload.api_enabled),
                SETTING_API_TOKEN_REVEAL_ENABLED: _dump_bool(payload.api_token_reveal_enabled),
                SETTING_DATA_JOB_MAX_WORKERS: str(payload.data_job_max_workers),
                SETTING_DATA_JOB_RETENTION_DAYS: str(payload.data_job_retention_days),
                SETTING_NAVIGATION_ORDER: json.dumps(_clean_navigation_order(payload.navigation_order)),
            }
        )
        after = _settings_snapshot(self.get_settings())
        record_audit(
            self.db,
            actor.id,
            "settings.update",
            "system_settings",
            "",
            after["app_name"],
            audit_detail(str(after["app_name"]), audit_changes(before, after)),
        )
        self.db.commit()
        return self.get_settings()

    def prune_audit_logs(self, retention_days: int | None = None) -> None:
        days = retention_days or self.get_settings().log_retention_days
        for actor_user_id in self._audit_actor_ids():
            latest = self._latest_audit_time(actor_user_id)
            if latest is None:
                continue
            threshold = latest - timedelta(days=days)
            query = self.db.query(AuditLog).filter(AuditLog.created_at < threshold)
            if actor_user_id is None:
                query = query.filter(AuditLog.actor_user_id.is_(None))
            else:
                query = query.filter(AuditLog.actor_user_id == actor_user_id)
            query.delete(synchronize_session=False)

    def backup_data(self, actor: User) -> bytes:
        backup = export_database(self.db)
        record_audit(
            self.db,
            actor.id,
            "settings.backup",
            "system_settings",
            "",
            "backup",
            audit_detail(
                "backup",
                meta={"tables": list_database_tables(self.db.get_bind()), "database_type": load_install_config().database_type},
            ),
        )
        self.db.commit()
        return backup

    def _merged_settings(self) -> SystemSettings:
        raw = self.settings.all()
        defaults = _default_settings()
        return SystemSettings(
            app_name=_clean_text(raw.get(SETTING_APP_NAME), defaults.app_name),
            registration_enabled=_parse_bool(raw.get(SETTING_REGISTRATION_ENABLED), defaults.registration_enabled),
            registration_approval_required=_parse_bool(
                raw.get(SETTING_REGISTRATION_APPROVAL_REQUIRED), defaults.registration_approval_required
            ),
            registration_required_fields=_parse_required_fields(raw.get(SETTING_REQUIRED_FIELDS), defaults.registration_required_fields),
            log_retention_days=_parse_retention_days(raw.get(SETTING_LOG_RETENTION_DAYS), defaults.log_retention_days),
            default_locale=_parse_locale(raw.get(SETTING_DEFAULT_LOCALE), defaults.default_locale),
            api_enabled=_parse_bool(raw.get(SETTING_API_ENABLED), defaults.api_enabled),
            api_token_reveal_enabled=_parse_bool(raw.get(SETTING_API_TOKEN_REVEAL_ENABLED), defaults.api_token_reveal_enabled),
            data_job_max_workers=_parse_int(
                raw.get(SETTING_DATA_JOB_MAX_WORKERS),
                defaults.data_job_max_workers,
                minimum=1,
                maximum=16,
            ),
            data_job_retention_days=_parse_retention_days(
                raw.get(SETTING_DATA_JOB_RETENTION_DAYS),
                defaults.data_job_retention_days,
            ),
            navigation_order=_parse_navigation_order(raw.get(SETTING_NAVIGATION_ORDER), defaults.navigation_order),
        )

    def _audit_actor_ids(self) -> list[int | None]:
        rows = self.db.query(AuditLog.actor_user_id).distinct().all()
        return [row[0] for row in rows]

    def _latest_audit_time(self, actor_user_id: int | None):
        query = self.db.query(AuditLog.created_at)
        if actor_user_id is None:
            query = query.filter(AuditLog.actor_user_id.is_(None))
        else:
            query = query.filter(AuditLog.actor_user_id == actor_user_id)
        row = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).first()
        return row[0] if row else None


def _default_settings() -> SystemSettings:
    return SystemSettings(
        app_name=get_settings().app_name,
        registration_enabled=True,
        registration_approval_required=True,
        registration_required_fields=RegistrationRequiredFields(),
        log_retention_days=DEFAULT_LOG_RETENTION_DAYS,
        default_locale="zh-CN",
        api_enabled=True,
        api_token_reveal_enabled=True,
        data_job_max_workers=DEFAULT_DATA_JOB_MAX_WORKERS,
        data_job_retention_days=DEFAULT_DATA_JOB_RETENTION_DAYS,
        navigation_order=[],
    )


def _settings_snapshot(settings: SystemSettings) -> dict[str, object]:
    return {
        "app_name": settings.app_name,
        "registration_enabled": settings.registration_enabled,
        "registration_approval_required": settings.registration_approval_required,
        "registration_required_fields": settings.registration_required_fields.model_dump(),
        "log_retention_days": settings.log_retention_days,
        "default_locale": settings.default_locale,
        "api_enabled": settings.api_enabled,
        "api_token_reveal_enabled": settings.api_token_reveal_enabled,
        "data_job_max_workers": settings.data_job_max_workers,
        "data_job_retention_days": settings.data_job_retention_days,
        "navigation_order": settings.navigation_order,
    }


def _clean_text(value: str | None, fallback: str) -> str:
    cleaned = value.strip() if value else ""
    return cleaned or fallback


def _dump_bool(value: bool) -> str:
    return "1" if value else "0"


def _parse_bool(value: str | None, fallback: bool) -> bool:
    if value is None:
        return fallback
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_required_fields(value: str | None, fallback: RegistrationRequiredFields) -> RegistrationRequiredFields:
    if not value:
        return fallback
    try:
        return RegistrationRequiredFields.model_validate_json(value)
    except ValueError:
        return fallback


def _parse_retention_days(value: str | None, fallback: int) -> int:
    try:
        days = int(value or "")
    except ValueError:
        return fallback
    return days if days in {7, 30, 90, 180, 365} else fallback


def _parse_locale(value: str | None, fallback: str):
    return value if value in {"zh-CN", "en-US"} else fallback


def _parse_navigation_order(value: str | None, fallback: list[str]) -> list[str]:
    if not value:
        return fallback
    try:
        parsed = json.loads(value)
    except ValueError:
        return fallback
    return _clean_navigation_order(parsed) if isinstance(parsed, list) else fallback


def _clean_navigation_order(value: list[object]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            continue
        key = item.strip()
        if not key or key in seen or not NAVIGATION_KEY_RE.match(key):
            continue
        seen.add(key)
        result.append(key)
    return result


def _parse_int(value: str | None, fallback: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or "")
    except ValueError:
        return fallback
    return min(max(parsed, minimum), maximum)
