from sqlalchemy.orm import Session

from app.repositories.audit import AuditRepository


def record_audit(
    db: Session,
    actor_user_id: int | None,
    action: str,
    target_type: str = "",
    target_id: str = "",
    detail: str = "",
) -> None:
    AuditRepository(db).add(actor_user_id, action, target_type, target_id, detail)
