from urllib.parse import quote

from fastapi import APIRouter, Depends, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import require_any_permission, require_permission, require_web_session
from app.db.session import get_db
from app.models import User
from app.modules.storage import STORAGE_CREATE, STORAGE_DELETE, STORAGE_OPERATE, STORAGE_READ, STORAGE_UPDATE
from app.modules.storage.schemas import (
    StorageConnectionItem,
    StorageConnectionListResponse,
    StorageConnectionPayload,
    StorageEntry,
    StorageFileListResponse,
    StorageMkdirRequest,
    StorageRenameRequest,
    StorageTestRequest,
)
from app.modules.storage.services import StorageService
from app.schemas.common import MessageResponse, message_response

router = APIRouter(prefix="/api/storages")
MANAGE_TAGS = ["storages"]
MANAGE_DEPENDENCIES = [Depends(require_web_session)]
FILE_TAGS = ["storage-files"]


@router.get("", response_model=StorageConnectionListResponse, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def list_storages(
    keyword: str = "",
    protocol: str = "",
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=500),
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_READ)),
) -> StorageConnectionListResponse:
    return StorageService(db).list_connections(actor, keyword, protocol, page, page_size)


@router.post("", response_model=StorageConnectionItem, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def create_storage(
    payload: StorageConnectionPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_CREATE)),
) -> StorageConnectionItem:
    return StorageService(db).create(actor, payload)


@router.post("/test", response_model=MessageResponse, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def test_storage(
    payload: StorageTestRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_any_permission(STORAGE_CREATE, STORAGE_UPDATE)),
) -> MessageResponse:
    StorageService(db).test_connection(actor, payload)
    return message_response("storage.connectionOk", "Storage connection is healthy")


@router.put("/{connection_id}", response_model=StorageConnectionItem, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def update_storage(
    connection_id: int,
    payload: StorageConnectionPayload,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_UPDATE)),
) -> StorageConnectionItem:
    return StorageService(db).update(actor, connection_id, payload)


@router.delete("/{connection_id}", response_model=MessageResponse, tags=MANAGE_TAGS, dependencies=MANAGE_DEPENDENCIES)
def delete_storage(
    connection_id: int,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_DELETE)),
) -> MessageResponse:
    StorageService(db).delete(actor, connection_id)
    return message_response("storage.deleted", "Storage connection deleted")


@router.get("/{storage_id}/files", response_model=StorageFileListResponse, tags=FILE_TAGS, summary="List directory entries")
def list_storage_files(
    storage_id: str,
    path: str = "/",
    keyword: str = "",
    recursive: bool = False,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_READ)),
) -> StorageFileListResponse:
    return StorageService(db).list_files(actor, storage_id, path, keyword, recursive)


@router.get("/{storage_id}/download", tags=FILE_TAGS, summary="Download a file")
def download_storage_file(
    storage_id: str,
    path: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_READ)),
) -> StreamingResponse:
    filename, stream = StorageService(db).download(actor, storage_id, path)
    return StreamingResponse(
        stream,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.post("/{storage_id}/upload", response_model=StorageEntry, tags=FILE_TAGS, summary="Upload a file")
def upload_storage_file(
    storage_id: str,
    file: UploadFile,
    path: str = "/",
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_OPERATE)),
) -> StorageEntry:
    return StorageService(db).upload(actor, storage_id, path, file.filename or "", file.file, file.size)


@router.post("/{storage_id}/mkdir", response_model=StorageEntry, tags=FILE_TAGS, summary="Create a directory")
def mkdir_storage(
    storage_id: str,
    payload: StorageMkdirRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_OPERATE)),
) -> StorageEntry:
    return StorageService(db).mkdir(actor, storage_id, payload.path)


@router.post("/{storage_id}/rename", response_model=StorageEntry, tags=FILE_TAGS, summary="Rename a file or directory")
def rename_storage_entry(
    storage_id: str,
    payload: StorageRenameRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_OPERATE)),
) -> StorageEntry:
    return StorageService(db).rename(actor, storage_id, payload.path, payload.new_name)


@router.delete("/{storage_id}/files", response_model=MessageResponse, tags=FILE_TAGS, summary="Delete a file or directory")
def delete_storage_entry(
    storage_id: str,
    path: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_permission(STORAGE_OPERATE)),
) -> MessageResponse:
    StorageService(db).delete_entry(actor, storage_id, path)
    return message_response("storage.entryDeleted", "Entry deleted")
