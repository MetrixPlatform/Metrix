from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import forbidden, not_found
from app.core.permissions import ANNOUNCEMENT_MANAGE_OTHERS
from app.models import Announcement, User
from app.repositories.announcements import AnnouncementRepository
from app.schemas.announcement import AnnouncementFeedItem, AnnouncementItem, AnnouncementListResponse, AnnouncementPayload
from app.services.audit import record_audit
from app.services.permissions import has_permission


class AnnouncementService:
    def __init__(self, db: Session):
        self.db = db
        self.announcements = AnnouncementRepository(db)

    def public_ticker(self) -> list[Announcement]:
        return self.announcements.public_ticker()

    def list_announcements(
        self,
        actor: User,
        keyword: str = "",
        target_type: str = "",
        display_mode: str = "",
        is_active: bool | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        created_by: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> AnnouncementListResponse:
        created_by_user_id = actor.id if created_by == "me" else None
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        announcements, total = self.announcements.list(
            keyword,
            target_type,
            display_mode,
            is_active,
            start_time,
            end_time,
            created_by_user_id,
            created_at_order,
            page,
            page_size,
        )
        return AnnouncementListResponse(
            items=self._with_creator_usernames(announcements),
            total=total,
            page=page,
            page_size=page_size,
        )

    def list_for_user(self, user: User) -> list[AnnouncementFeedItem]:
        reads = self.announcements.read_map(user.id)
        items = []
        for announcement in self.announcements.active():
            if not self._matches_user(announcement, user):
                continue
            read = reads.get(announcement.id)
            items.append(
                AnnouncementFeedItem.model_validate(announcement).model_copy(
                    update={"is_read": read is not None, "read_at": read.read_at if read else None}
                )
            )
        return items

    def create(self, actor: User, payload: AnnouncementPayload) -> AnnouncementItem:
        announcement = self.announcements.create(
            Announcement(
                title=payload.title,
                content=payload.content,
                target_type=payload.target_type,
                target_value=self._normalized_target_value(payload),
                show_popup=payload.show_popup,
                show_ticker=payload.show_ticker,
                show_sidebar=payload.show_sidebar,
                is_active=payload.is_active,
                created_by=actor.id,
            )
        )
        record_audit(self.db, actor.id, "announcement.create", "announcement", str(announcement.id), announcement.title)
        self.db.commit()
        return self._with_creator_username(announcement, actor.username)

    def update(self, actor: User, announcement_id: int, payload: AnnouncementPayload) -> AnnouncementItem:
        announcement = self._get(announcement_id)
        self._ensure_can_manage(actor, announcement)
        announcement.title = payload.title
        announcement.content = payload.content
        announcement.target_type = payload.target_type
        announcement.target_value = self._normalized_target_value(payload)
        announcement.show_popup = payload.show_popup
        announcement.show_ticker = payload.show_ticker
        announcement.show_sidebar = payload.show_sidebar
        announcement.is_active = payload.is_active
        record_audit(self.db, actor.id, "announcement.update", "announcement", str(announcement.id), announcement.title)
        self.db.commit()
        creator_name = actor.username if announcement.created_by == actor.id else self._creator_username(announcement)
        return self._with_creator_username(announcement, creator_name)

    def delete(self, actor: User, announcement_id: int) -> None:
        announcement = self._get(announcement_id)
        self._ensure_can_manage(actor, announcement)
        record_audit(self.db, actor.id, "announcement.delete", "announcement", str(announcement.id), announcement.title)
        self.announcements.delete(announcement)
        self.db.commit()

    def batch_delete(self, actor: User, announcement_ids: list[int]) -> int:
        deleted_count = 0
        for announcement_id in dict.fromkeys(announcement_ids):
            announcement = self._get(announcement_id)
            self._ensure_can_manage(actor, announcement)
            record_audit(self.db, actor.id, "announcement.delete", "announcement", str(announcement.id), announcement.title)
            self.announcements.delete(announcement)
            deleted_count += 1
        self.db.commit()
        return deleted_count

    def mark_read(self, user: User, announcement_id: int) -> AnnouncementFeedItem:
        announcement = self._get(announcement_id)
        if not announcement.is_active or not self._matches_user(announcement, user):
            raise not_found("error.announcementNotFound", "Announcement not found")
        read = self.announcements.mark_read(announcement.id, user.id)
        self.db.commit()
        return AnnouncementFeedItem.model_validate(announcement).model_copy(update={"is_read": True, "read_at": read.read_at})

    def _get(self, announcement_id: int) -> Announcement:
        announcement = self.announcements.get(announcement_id)
        if announcement is None:
            raise not_found("error.announcementNotFound", "Announcement not found")
        return announcement

    def _ensure_can_manage(self, actor: User, announcement: Announcement) -> None:
        if announcement.created_by == actor.id:
            return
        if has_permission(actor, ANNOUNCEMENT_MANAGE_OTHERS):
            return
        raise forbidden("error.announcementManageOthersDenied", "You cannot manage announcements created by others")

    def _matches_user(self, announcement: Announcement, user: User) -> bool:
        target_type = announcement.target_type
        if target_type in {"all", "authenticated"}:
            return True
        targets = self._split_targets(announcement.target_value)
        if target_type == "permission":
            return any(has_permission(user, code) for code in targets)
        if target_type == "company":
            return user.company in targets
        if target_type == "company_department":
            return any(self._matches_company_department(target, user) for target in targets)
        if target_type == "user":
            return user.username in targets
        return False

    def _normalized_target_value(self, payload: AnnouncementPayload) -> str:
        return "" if payload.target_type in {"all", "authenticated"} else payload.target_value.strip()

    def _split_targets(self, value: str) -> list[str]:
        normalized = value.replace("\n", ",")
        return [item.strip() for item in normalized.split(",") if item.strip()]

    def _matches_company_department(self, target: str, user: User) -> bool:
        company, _, department = target.partition("|")
        return company == user.company and department == user.department

    def _with_creator_usernames(self, announcements: list[Announcement]) -> list[AnnouncementItem]:
        user_ids = {announcement.created_by for announcement in announcements if announcement.created_by is not None}
        usernames = self.announcements.creator_usernames(user_ids)
        return [
            self._with_creator_username(announcement, usernames.get(announcement.created_by, ""))
            for announcement in announcements
        ]

    def _with_creator_username(self, announcement: Announcement, username: str) -> AnnouncementItem:
        return AnnouncementItem.model_validate(announcement).model_copy(update={"created_by_username": username})

    def _creator_username(self, announcement: Announcement) -> str:
        if announcement.created_by is None:
            return ""
        return self.announcements.creator_usernames({announcement.created_by}).get(announcement.created_by, "")
