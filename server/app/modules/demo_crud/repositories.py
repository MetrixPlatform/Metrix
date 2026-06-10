from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import User
from app.modules.demo_crud.models import DemoItem


class DemoItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, item_id: int) -> DemoItem | None:
        return self.db.get(DemoItem, item_id)

    def list(
        self,
        keyword: str = "",
        category: str = "",
        is_active: bool | None = None,
        created_by_user_id: int | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[DemoItem], int]:
        query = self.db.query(DemoItem)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(or_(DemoItem.name.ilike(pattern), DemoItem.description.ilike(pattern)))
        if category:
            query = query.filter(DemoItem.category == category)
        if is_active is not None:
            query = query.filter(DemoItem.is_active == is_active)
        if created_by_user_id is not None:
            query = query.filter(DemoItem.created_by == created_by_user_id)
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(DemoItem.created_at.asc(), DemoItem.id.asc())
        else:
            query = query.order_by(DemoItem.created_at.desc(), DemoItem.id.desc())
        return query.offset((page - 1) * page_size).limit(page_size).all(), total

    def create(self, item: DemoItem) -> DemoItem:
        self.db.add(item)
        self.db.flush()
        return item

    def delete(self, item: DemoItem) -> None:
        self.db.delete(item)
        self.db.flush()

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}
