from datetime import datetime
import csv
import json
from io import StringIO
from typing import Any, Mapping

from sqlalchemy.orm import Session

from app.core.auth_context import auth_api_token_prefix, auth_source
from app.core.exceptions import forbidden
from app.core.permissions import AUDIT_LOG_MANAGE_OTHERS
from app.models import AuditLog, User
from app.repositories.audit import AuditRepository
from app.schemas.audit import AuditLogItem, AuditLogListResponse
from app.services.permissions import has_permission


def record_audit(
    db: Session,
    actor_user_id: int | None,
    action: str,
    target_type: str = "",
    target_id: str = "",
    detail: str = "",
    detail_data: Mapping[str, Any] | None = None,
) -> None:
    AuditRepository(db).add(
        actor_user_id,
        action,
        target_type,
        target_id,
        detail,
        _dump_detail_data(detail_data),
        auth_source(db),
        auth_api_token_prefix(db),
    )


def audit_detail(
    target_name: str = "",
    changes: list[dict[str, Any]] | None = None,
    meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if target_name:
        data["target_name"] = target_name
    if changes:
        data["changes"] = changes
    if meta:
        data["meta"] = {key: _json_value(value) for key, value in meta.items()}
    return data


def audit_changes(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[dict[str, Any]]:
    changes = []
    for field, before_value in before.items():
        after_value = after.get(field)
        if _json_value(before_value) != _json_value(after_value):
            changes.append({"field": field, "before": _json_value(before_value), "after": _json_value(after_value)})
    return changes


class AuditService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_logs = AuditRepository(db)

    def list_logs(
        self,
        actor: User,
        actor_scope: str = "self",
        keyword: str = "",
        action: str = "",
        target_type: str = "",
        source: str = "",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> AuditLogListResponse:
        actor_user_id = self._actor_user_id(actor, actor_scope)
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        logs, total = self.audit_logs.list(
            actor_user_id,
            keyword,
            action,
            target_type,
            source,
            start_time,
            end_time,
            created_at_order,
            page,
            page_size,
        )
        return AuditLogListResponse(items=self._with_actor_usernames(logs), total=total, page=page, page_size=page_size)

    def export_csv(
        self,
        actor: User,
        actor_scope: str = "self",
        keyword: str = "",
        action: str = "",
        target_type: str = "",
        source: str = "",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        sort_order: str = "descend",
    ) -> str:
        actor_user_id = self._actor_user_id(actor, actor_scope)
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        logs = self.audit_logs.export(
            actor_user_id,
            keyword,
            action,
            target_type,
            source,
            start_time,
            end_time,
            created_at_order,
        )
        return self._csv_text(self._with_actor_usernames(logs))

    def _actor_user_id(self, actor: User, actor_scope: str) -> int | None:
        if actor_scope == "all":
            if has_permission(actor, AUDIT_LOG_MANAGE_OTHERS):
                return None
            raise forbidden("error.auditLogManageOthersDenied", "You cannot view audit logs created by others")
        return actor.id

    def _with_actor_usernames(self, logs: list[AuditLog]) -> list[AuditLogItem]:
        user_ids = {log.actor_user_id for log in logs if log.actor_user_id is not None}
        usernames = self.audit_logs.actor_usernames(user_ids)
        return [
            AuditLogItem.model_validate(log).model_copy(update={"actor_username": usernames.get(log.actor_user_id, "")})
            for log in logs
        ]

    def _csv_text(self, logs: list[AuditLogItem]) -> str:
        output = StringIO()
        output.write("\ufeff")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(["id", "operator", "source", "api_token_prefix", "action", "target_type", "target_id", "detail", "created_at"])
        for log in logs:
            writer.writerow(
                [
                    log.id,
                    log.actor_username or "system",
                    log.source,
                    log.api_token_prefix,
                    log.action,
                    log.target_type,
                    log.target_id,
                    log.detail,
                    log.created_at.isoformat(sep=" "),
                ]
            )
        return output.getvalue()


def _dump_detail_data(detail_data: Mapping[str, Any] | None) -> str:
    if not detail_data:
        return ""
    return json.dumps(detail_data, ensure_ascii=False, default=str, separators=(",", ":"))


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    return value
