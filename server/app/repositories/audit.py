from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import AuditLog, User


class AuditRepository:
    def __init__(self, db: Session):
        self.db = db

    def add(
        self,
        actor_user_id: int | None,
        action: str,
        target_type: str = "",
        target_id: str = "",
        detail: str = "",
        detail_data: str = "",
        source: str = "web",
        api_token_prefix: str = "",
    ) -> None:
        self.db.add(
            AuditLog(
                actor_user_id=actor_user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                detail=detail,
                detail_data=detail_data,
                source=source,
                api_token_prefix=api_token_prefix,
            )
        )
        self.db.flush()

    def list(
        self,
        actor_user_id: int | None = None,
        keyword: str = "",
        action: Sequence[str] | None = None,
        target_type: Sequence[str] | None = None,
        source: Sequence[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AuditLog], int]:
        query = self._filtered_query(actor_user_id, keyword, action, target_type, source, start_time, end_time)
        total = query.count()
        query = self._ordered_query(query, created_at_order)
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all(), total

    def export(
        self,
        actor_user_id: int | None = None,
        keyword: str = "",
        action: Sequence[str] | None = None,
        target_type: Sequence[str] | None = None,
        source: Sequence[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        created_at_order: str = "descend",
    ) -> list[AuditLog]:
        query = self._filtered_query(actor_user_id, keyword, action, target_type, source, start_time, end_time)
        return self._ordered_query(query, created_at_order).all()

    def actor_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}

    def _filtered_query(
        self,
        actor_user_id: int | None = None,
        keyword: str = "",
        action: Sequence[str] | None = None,
        target_type: Sequence[str] | None = None,
        source: Sequence[str] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ):
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
                    AuditLog.detail_data.ilike(pattern),
                )
            )
        actions = _normalized_values(action)
        target_types = _normalized_values(target_type)
        sources = _normalized_values(source)
        if actions:
            query = query.filter(AuditLog.action.in_(actions))
        if target_types:
            query = query.filter(AuditLog.target_type.in_(target_types))
        if sources:
            query = query.filter(AuditLog.source.in_(sources))
        if start_time:
            query = query.filter(AuditLog.created_at >= start_time)
        if end_time:
            query = query.filter(AuditLog.created_at <= end_time)
        return query

    def _ordered_query(self, query, created_at_order: str):
        if created_at_order == "ascend":
            return query.order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        return query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())


def _normalized_values(values: Sequence[str] | None) -> list[str]:
    return [item.strip() for item in values or [] if item and item.strip()]
