from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import AuditLog, User


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

    def list(
        self,
        actor_user_id: int | None = None,
        keyword: str = "",
        action: str = "",
        target_type: str = "",
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        query = self.db.query(AuditLog).outerjoin(User, User.id == AuditLog.actor_user_id)
        if actor_user_id is not None:
            query = query.filter(AuditLog.actor_user_id == actor_user_id)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    User.username.ilike(pattern),
                    AuditLog.action.ilike(pattern),
                    AuditLog.target_type.ilike(pattern),
                    AuditLog.target_id.ilike(pattern),
                    AuditLog.detail.ilike(pattern),
                )
            )
        if action:
            query = query.filter(AuditLog.action == action)
        if target_type:
            query = query.filter(AuditLog.target_type == target_type)
        if start_time:
            query = query.filter(AuditLog.created_at >= start_time)
        if end_time:
            query = query.filter(AuditLog.created_at <= end_time)
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        else:
            query = query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all(), total

    def actor_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}
