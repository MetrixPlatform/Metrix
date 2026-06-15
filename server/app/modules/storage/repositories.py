from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import User
from app.modules.storage.models import StorageConnection


class StorageConnectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, connection_id: int) -> StorageConnection | None:
        return self.db.get(StorageConnection, connection_id)

    def get_by_storage_id(self, storage_id: str) -> StorageConnection | None:
        return self.db.query(StorageConnection).filter(StorageConnection.storage_id == storage_id).first()

    def list(
        self,
        keyword: str = "",
        protocol: str = "",
        is_shared: bool | None = None,
        is_active: bool | None = None,
        created_by_user_id: int | None = None,
        visible_to_user_id: int | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[StorageConnection], int]:
        query = self.db.query(StorageConnection)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.outerjoin(User, User.id == StorageConnection.created_by)
            query = query.filter(
                or_(
                    StorageConnection.name.ilike(pattern),
                    StorageConnection.storage_id.ilike(pattern),
                    StorageConnection.host.ilike(pattern),
                    User.username.ilike(pattern),
                    User.full_name.ilike(pattern),
                )
            )
        if protocol:
            query = query.filter(StorageConnection.protocol == protocol)
        if is_shared is not None:
            query = query.filter(StorageConnection.is_shared == is_shared)
        if is_active is not None:
            query = query.filter(StorageConnection.is_active == is_active)
        if created_by_user_id is not None:
            query = query.filter(StorageConnection.created_by == created_by_user_id)
        if visible_to_user_id is not None:
            query = query.filter(
                or_(StorageConnection.created_by == visible_to_user_id, StorageConnection.is_shared.is_(True))
            )
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(StorageConnection.created_at.asc(), StorageConnection.id.asc())
        else:
            query = query.order_by(StorageConnection.created_at.desc(), StorageConnection.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def create(self, connection: StorageConnection) -> StorageConnection:
        self.db.add(connection)
        self.db.flush()
        return connection

    def delete(self, connection: StorageConnection) -> None:
        self.db.delete(connection)
        self.db.flush()

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}
