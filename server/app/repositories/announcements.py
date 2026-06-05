from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Announcement, AnnouncementRead, User


class AnnouncementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, announcement_id: int) -> Announcement | None:
        return self.db.get(Announcement, announcement_id)

    def list(
        self,
        keyword: str = "",
        target_type: str = "",
        display_mode: str = "",
        is_active: bool | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[Announcement]:
        query = self.db.query(Announcement)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(or_(Announcement.title.ilike(pattern), Announcement.content.ilike(pattern)))
        if target_type:
            query = query.filter(Announcement.target_type == target_type)
        if display_mode == "popup":
            query = query.filter(Announcement.show_popup.is_(True))
        elif display_mode == "ticker":
            query = query.filter(Announcement.show_ticker.is_(True))
        elif display_mode == "sidebar":
            query = query.filter(Announcement.show_sidebar.is_(True))
        if is_active is not None:
            query = query.filter(Announcement.is_active == is_active)
        if start_time is not None:
            query = query.filter(Announcement.created_at >= start_time)
        if end_time is not None:
            query = query.filter(Announcement.created_at <= end_time)
        return query.order_by(Announcement.created_at.desc(), Announcement.id.desc()).all()

    def active(self) -> list[Announcement]:
        return (
            self.db.query(Announcement)
            .filter(Announcement.is_active.is_(True))
            .order_by(Announcement.created_at.desc(), Announcement.id.desc())
            .all()
        )

    def public_ticker(self) -> list[Announcement]:
        return (
            self.db.query(Announcement)
            .filter(
                Announcement.is_active.is_(True),
                Announcement.target_type == "all",
                Announcement.show_ticker.is_(True),
            )
            .order_by(Announcement.created_at.desc(), Announcement.id.desc())
            .all()
        )

    def create(self, announcement: Announcement) -> Announcement:
        self.db.add(announcement)
        self.db.flush()
        return announcement

    def delete(self, announcement: Announcement) -> None:
        self.db.delete(announcement)
        self.db.flush()

    def read_map(self, user_id: int) -> dict[int, AnnouncementRead]:
        reads = self.db.query(AnnouncementRead).filter(AnnouncementRead.user_id == user_id).all()
        return {read.announcement_id: read for read in reads}

    def mark_read(self, announcement_id: int, user_id: int) -> AnnouncementRead:
        read = (
            self.db.query(AnnouncementRead)
            .filter(AnnouncementRead.announcement_id == announcement_id, AnnouncementRead.user_id == user_id)
            .first()
        )
        if read is None:
            read = AnnouncementRead(announcement_id=announcement_id, user_id=user_id)
            self.db.add(read)
            self.db.flush()
        return read

    def creator_usernames(self, user_ids: set[int]) -> dict[int, str]:
        if not user_ids:
            return {}
        rows = self.db.query(User.id, User.username).filter(User.id.in_(user_ids)).all()
        return {user_id: username for user_id, username in rows}
