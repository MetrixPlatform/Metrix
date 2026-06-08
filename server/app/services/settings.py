from __future__ import annotations

import json
import zipfile
from datetime import date, datetime, timedelta
from io import BytesIO

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.install import load_install_config
from app.models import AuditLog, User
from app.repositories.settings import SystemSettingRepository
from app.schemas.settings import PublicSettings, RegistrationRequiredFields, SystemSettings, SystemSettingsUpdate
from app.services.audit import audit_changes, audit_detail, record_audit

SETTING_APP_NAME = "app_name"
SETTING_REGISTRATION_ENABLED = "registration_enabled"
SETTING_REGISTRATION_APPROVAL_REQUIRED = "registration_approval_required"
SETTING_REQUIRED_FIELDS = "registration_required_fields"
SETTING_LOG_RETENTION_DAYS = "log_retention_days"
SETTING_DEFAULT_LOCALE = "default_locale"
SETTING_API_ENABLED = "api_enabled"
SETTING_API_TOKEN_REVEAL_ENABLED = "api_token_reveal_enabled"
DEFAULT_LOG_RETENTION_DAYS = 90
BACKUP_TABLES = [
    "users",
    "roles",
    "permissions",
    "user_roles",
    "role_permissions",
    "audit_logs",
    "announcements",
    "announcement_reads",
    "api_tokens",
    "system_settings",
]


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
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as backup:
            backup.writestr("metadata.json", self._backup_metadata())
            for table in BACKUP_TABLES:
                if self._table_exists(table):
                    backup.writestr(f"tables/{table}.json", json.dumps(self._table_rows(table), ensure_ascii=False, indent=2))
        record_audit(
            self.db,
            actor.id,
            "settings.backup",
            "system_settings",
            "",
            "backup",
            audit_detail("backup", meta={"tables": BACKUP_TABLES, "database_type": load_install_config().database_type}),
        )
        self.db.commit()
        return buffer.getvalue()

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

    def _backup_metadata(self) -> str:
        payload = {
            "app_name": self.get_settings().app_name,
            "database_type": load_install_config().database_type,
            "exported_by": "Metrix",
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def _table_exists(self, table: str) -> bool:
        bind = self.db.get_bind()
        dialect = bind.dialect.name
        if dialect == "sqlite":
            result = self.db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table"), {"table": table})
        else:
            result = self.db.execute(text("SHOW TABLES LIKE :table"), {"table": table})
        return result.first() is not None

    def _table_rows(self, table: str) -> list[dict[str, object]]:
        safe_table = table.replace("`", "")
        rows = self.db.execute(text(f"SELECT * FROM `{safe_table}`")).mappings().all()
        return [{key: _json_value(value) for key, value in dict(row).items()} for row in rows]


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


def _json_value(value: object) -> object:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
