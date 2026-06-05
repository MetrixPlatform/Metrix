from datetime import datetime

from sqlalchemy.orm import Session

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
) -> None:
    AuditRepository(db).add(actor_user_id, action, target_type, target_id, detail)


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
            start_time,
            end_time,
            created_at_order,
            page,
            page_size,
        )
        return AuditLogListResponse(items=self._with_actor_usernames(logs), total=total, page=page, page_size=page_size)

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
