from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.permissions import ADMIN_ROLE
from app.models import Role, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.query(User).filter(User.username == username).first()

    def list(
        self,
        keyword: str = "",
        approval_status: str = "",
        is_active: bool | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        created_at_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        query = self.db.query(User)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    User.username.ilike(pattern),
                    User.full_name.ilike(pattern),
                    User.phone.ilike(pattern),
                    User.email.ilike(pattern),
                    User.company.ilike(pattern),
                    User.department.ilike(pattern),
                )
            )
        if approval_status:
            query = query.filter(User.approval_status == approval_status)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)
        if start_time:
            query = query.filter(User.created_at >= start_time)
        if end_time:
            query = query.filter(User.created_at <= end_time)
        total = query.count()
        if created_at_order == "ascend":
            query = query.order_by(User.created_at.asc(), User.id.asc())
        else:
            query = query.order_by(User.created_at.desc(), User.id.desc())
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size).all(), total

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def count_admins(self) -> int:
        return (
            self.db.query(User)
            .join(User.roles)
            .filter(Role.code == ADMIN_ROLE, User.is_active.is_(True), User.approval_status == "approved")
            .count()
        )

    def count(self, approval_status: str = "") -> int:
        query = self.db.query(User)
        if approval_status:
            query = query.filter(User.approval_status == approval_status)
        return query.count()
