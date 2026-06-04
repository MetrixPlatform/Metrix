from sqlalchemy.orm import Session

from app.models import Announcement, AnnouncementRead


class AnnouncementRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, announcement_id: int) -> Announcement | None:
        return self.db.get(Announcement, announcement_id)

    def list(self) -> list[Announcement]:
        return self.db.query(Announcement).order_by(Announcement.created_at.desc(), Announcement.id.desc()).all()

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
