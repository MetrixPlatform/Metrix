from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_permission
from app.db.session import get_db
from app.models import User
from app.modules.demo_crud import DEMO_ITEM_CREATE, DEMO_ITEM_DELETE, DEMO_ITEM_READ, DEMO_ITEM_UPDATE
from app.modules.demo_crud.schemas import DemoItemItem, DemoItemListResponse, DemoItemPayload
from app.modules.demo_crud.services import DemoItemService
from app.schemas.common import MessageResponse, message_response

router = APIRouter(prefix="/api/demo-items", tags=["demo-items"])


@router.get("", response_model=DemoItemListResponse)
def list_demo_items(
    keyword: str = "",
    category: str = "",
    is_active: bool | None = None,
    created_by: str = "",
    sort_order: str = "descend",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DEMO_ITEM_READ)),
) -> DemoItemListResponse:
    return DemoItemService(db).list_items(actor, keyword, category, is_active, created_by, sort_order, page, page_size)


@router.post("", response_model=DemoItemItem)
def create_demo_item(
    payload: DemoItemPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DEMO_ITEM_CREATE)),
) -> DemoItemItem:
    return DemoItemService(db).create(actor, payload)


@router.put("/{item_id}", response_model=DemoItemItem)
def update_demo_item(
    item_id: int,
    payload: DemoItemPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DEMO_ITEM_UPDATE)),
) -> DemoItemItem:
    return DemoItemService(db).update(actor, item_id, payload)


@router.delete("/{item_id}", response_model=MessageResponse)
def delete_demo_item(
    item_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(DEMO_ITEM_DELETE)),
) -> MessageResponse:
    DemoItemService(db).delete(actor, item_id)
    return message_response("demoCrud.deleted", "Demo item deleted")
