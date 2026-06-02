from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, actor_user_id: int | None, action: str, target_type: str = "", target_id: str = "", detail: str = "") -> None:
        self.db.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
            )
        )
        self.db.flush()
