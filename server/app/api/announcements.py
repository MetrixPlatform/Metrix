from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.core.permissions import ANNOUNCEMENT_CREATE, ANNOUNCEMENT_DELETE, ANNOUNCEMENT_READ, ANNOUNCEMENT_UPDATE
from app.db.session import get_db
from app.models import Announcement, User
from app.schemas.announcement import AnnouncementFeedItem, AnnouncementItem, AnnouncementPayload, PublicAnnouncementItem
from app.schemas.common import MessageResponse
from app.services.announcements import AnnouncementService

router = APIRouter(prefix="/api/announcements", tags=["announcements"])


@router.get("/public", response_model=list[PublicAnnouncementItem])
def public_announcements(db: Session = Depends(get_db)) -> list[Announcement]:
    return AnnouncementService(db).public_ticker()


@router.get("/mine", response_model=list[AnnouncementFeedItem])
def my_announcements(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AnnouncementFeedItem]:
    return AnnouncementService(db).list_for_user(user)


@router.post("/{announcement_id}/read", response_model=AnnouncementFeedItem)
def mark_announcement_read(
    announcement_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AnnouncementFeedItem:
    return AnnouncementService(db).mark_read(user, announcement_id)


@router.get("", response_model=list[AnnouncementItem])
def list_announcements(
    db: Session = Depends(get_db),
    _: User = Depends(require_permission(ANNOUNCEMENT_READ)),
) -> list[Announcement]:
    return AnnouncementService(db).list_announcements()


@router.post("", response_model=AnnouncementItem)
def create_announcement(
    payload: AnnouncementPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_CREATE)),
) -> Announcement:
    return AnnouncementService(db).create(actor, payload)


@router.put("/{announcement_id}", response_model=AnnouncementItem)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_UPDATE)),
) -> Announcement:
    return AnnouncementService(db).update(actor, announcement_id, payload)


@router.delete("/{announcement_id}", response_model=MessageResponse)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_DELETE)),
) -> MessageResponse:
    AnnouncementService(db).delete(actor, announcement_id)
    return MessageResponse(message="公告已删除")
