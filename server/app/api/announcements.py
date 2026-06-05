from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_permission
from app.core.permissions import ANNOUNCEMENT_CREATE, ANNOUNCEMENT_DELETE, ANNOUNCEMENT_READ, ANNOUNCEMENT_UPDATE
from app.db.session import get_db
from app.models import Announcement, User
from app.schemas.announcement import (
    AnnouncementBatchDeleteRequest,
    AnnouncementFeedItem,
    AnnouncementItem,
    AnnouncementListResponse,
    AnnouncementPayload,
    PublicAnnouncementItem,
)
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


@router.get("", response_model=AnnouncementListResponse)
def list_announcements(
    keyword: str = "",
    target_type: str = "",
    display_mode: str = "",
    is_active: bool | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    created_by: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_READ)),
) -> AnnouncementListResponse:
    return AnnouncementService(db).list_announcements(
        actor,
        keyword,
        target_type,
        display_mode,
        is_active,
        start_time,
        end_time,
        created_by,
        sort_order,
        page,
        page_size,
    )


@router.post("", response_model=AnnouncementItem)
def create_announcement(
    payload: AnnouncementPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_CREATE)),
) -> AnnouncementItem:
    return AnnouncementService(db).create(actor, payload)


@router.post("/batch-delete", response_model=MessageResponse)
def batch_delete_announcements(
    payload: AnnouncementBatchDeleteRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_DELETE)),
) -> MessageResponse:
    deleted_count = AnnouncementService(db).batch_delete(actor, payload.ids)
    return MessageResponse(message=f"已删除 {deleted_count} 条公告")


@router.put("/{announcement_id}", response_model=AnnouncementItem)
def update_announcement(
    announcement_id: int,
    payload: AnnouncementPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_UPDATE)),
) -> AnnouncementItem:
    return AnnouncementService(db).update(actor, announcement_id, payload)


@router.delete("/{announcement_id}", response_model=MessageResponse)
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(ANNOUNCEMENT_DELETE)),
) -> MessageResponse:
    AnnouncementService(db).delete(actor, announcement_id)
    return MessageResponse(message="公告已删除")
