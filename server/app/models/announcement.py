from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utc_now
from app.db.base import Base


class Announcement(Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(Text)
    target_type: Mapped[str] = mapped_column(String(30), default="all", index=True)
    target_value: Mapped[str] = mapped_column(Text, default="")
    show_popup: Mapped[bool] = mapped_column(Boolean, default=False)
    show_ticker: Mapped[bool] = mapped_column(Boolean, default=True)
    show_sidebar: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    reads: Mapped[list["AnnouncementRead"]] = relationship(
        "AnnouncementRead",
        back_populates="announcement",
        cascade="all, delete-orphan",
    )


class AnnouncementRead(Base):
    __tablename__ = "announcement_reads"
    __table_args__ = (UniqueConstraint("announcement_id", "user_id", name="uq_announcement_read_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    announcement_id: Mapped[int] = mapped_column(Integer, ForeignKey("announcements.id"))
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    read_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    announcement: Mapped[Announcement] = relationship("Announcement", back_populates="reads")
