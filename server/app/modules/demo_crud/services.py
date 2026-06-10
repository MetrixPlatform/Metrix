from sqlalchemy.orm import Session

from app.core.exceptions import forbidden, not_found
from app.models import User
from app.modules.demo_crud import DEMO_ITEM_MANAGE_OTHERS
from app.modules.demo_crud.models import DemoItem
from app.modules.demo_crud.repositories import DemoItemRepository
from app.modules.demo_crud.schemas import DemoItemItem, DemoItemListResponse, DemoItemPayload
from app.services.audit import audit_changes, audit_detail, record_audit
from app.services.permissions import has_permission


class DemoItemService:
    def __init__(self, db: Session):
        self.db = db
        self.items = DemoItemRepository(db)

    def list_items(
        self,
        actor: User,
        keyword: str = "",
        category: str = "",
        is_active: bool | None = None,
        created_by: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> DemoItemListResponse:
        created_by_user_id = actor.id if created_by == "me" else None
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        items, total = self.items.list(
            keyword,
            category,
            is_active,
            created_by_user_id,
            created_at_order,
            page,
            page_size,
        )
        return DemoItemListResponse(
            items=self._with_creator_usernames(items),
            total=total,
            page=page,
            page_size=page_size,
        )

    def create(self, actor: User, payload: DemoItemPayload) -> DemoItemItem:
        item = self.items.create(
            DemoItem(
                name=payload.name,
                category=payload.category,
                description=payload.description,
                is_active=payload.is_active,
                created_by=actor.id,
            )
        )
        record_audit(
            self.db,
            actor.id,
            "demo_item.create",
            "demo_item",
            str(item.id),
            item.name,
            audit_detail(item.name, meta=_demo_item_snapshot(item)),
        )
        self.db.commit()
        return self._with_creator_username(item, actor.username)

    def update(self, actor: User, item_id: int, payload: DemoItemPayload) -> DemoItemItem:
        item = self._get(item_id)
        self._ensure_can_manage(actor, item)
        before = _demo_item_snapshot(item)
        item.name = payload.name
        item.category = payload.category
        item.description = payload.description
        item.is_active = payload.is_active
        record_audit(
            self.db,
            actor.id,
            "demo_item.update",
            "demo_item",
            str(item.id),
            item.name,
            audit_detail(item.name, audit_changes(before, _demo_item_snapshot(item))),
        )
        self.db.commit()
        creator_name = actor.username if item.created_by == actor.id else self._creator_username(item)
        return self._with_creator_username(item, creator_name)

    def delete(self, actor: User, item_id: int) -> None:
        item = self._get(item_id)
        self._ensure_can_manage(actor, item)
        record_audit(
            self.db,
            actor.id,
            "demo_item.delete",
            "demo_item",
            str(item.id),
            item.name,
            audit_detail(item.name, meta=_demo_item_snapshot(item)),
        )
        self.items.delete(item)
        self.db.commit()

    def _get(self, item_id: int) -> DemoItem:
        item = self.items.get(item_id)
        if item is None:
            raise not_found("error.demoItemNotFound", "Demo item not found")
        return item

    def _ensure_can_manage(self, actor: User, item: DemoItem) -> None:
        if item.created_by == actor.id:
            return
        if has_permission(actor, DEMO_ITEM_MANAGE_OTHERS):
            return
        raise forbidden("error.demoItemManageOthersDenied", "You cannot manage demo items created by others")

    def _with_creator_usernames(self, items: list[DemoItem]) -> list[DemoItemItem]:
        user_ids = {item.created_by for item in items if item.created_by is not None}
        usernames = self.items.creator_usernames(user_ids)
        return [self._with_creator_username(item, usernames.get(item.created_by, "")) for item in items]

    def _with_creator_username(self, item: DemoItem, username: str) -> DemoItemItem:
        return DemoItemItem.model_validate(item).model_copy(update={"created_by_username": username})

    def _creator_username(self, item: DemoItem) -> str:
        if item.created_by is None:
            return ""
        return self.items.creator_usernames({item.created_by}).get(item.created_by, "")


def _demo_item_snapshot(item: DemoItem) -> dict[str, object]:
    return {
        "name": item.name,
        "category": item.category,
        "description": item.description,
        "is_active": item.is_active,
    }
