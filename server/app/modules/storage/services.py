from __future__ import annotations

import posixpath
import secrets
from collections.abc import Iterator
from typing import BinaryIO

from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden, not_found, service_unavailable
from app.core.security import decrypt_secret, encrypt_secret
from app.models import User
from app.modules.storage import STORAGE_MANAGE_OTHERS
from app.modules.storage import clients as storage_clients
from app.modules.storage.clients import StorageClient, StorageConnectError, StorageOperationError
from app.modules.storage.models import StorageConnection
from app.modules.storage.repositories import StorageConnectionRepository
from app.modules.storage.schemas import (
    ENTRY_NAME_INVALID_CHARS,
    StorageConnectionItem,
    StorageConnectionListResponse,
    StorageConnectionPayload,
    StorageEntry,
    StorageFileListResponse,
    StorageTestRequest,
)
from app.services.audit import audit_changes, audit_detail, record_audit
from app.services.permissions import has_permission

GENERATED_ID_PREFIX = "stg_"
RECURSIVE_MAX_ENTRIES = 1000
RECURSIVE_MAX_DIRS = 500
MAX_TREE_DEPTH = 64


class StorageService:
    def __init__(self, db: Session):
        self.db = db
        self.storages = StorageConnectionRepository(db)

    def list_connections(
        self,
        actor: User,
        keyword: str = "",
        protocol: str = "",
        page: int = 1,
        page_size: int = 20,
    ) -> StorageConnectionListResponse:
        visible_to = None if has_permission(actor, STORAGE_MANAGE_OTHERS) else actor.id
        rows, total = self.storages.list(keyword, protocol, visible_to, page, page_size)
        return StorageConnectionListResponse(
            items=self._with_creator_usernames(rows),
            total=total,
            page=page,
            page_size=page_size,
        )

    def create(self, actor: User, payload: StorageConnectionPayload) -> StorageConnectionItem:
        if not payload.password:
            raise bad_request("error.storagePasswordRequired", "Password is required")
        storage_id = payload.storage_id or self._generate_storage_id()
        if self.storages.get_by_storage_id(storage_id) is not None:
            raise bad_request("error.storageIdTaken", "Storage ID already exists")
        connection = self.storages.create(
            StorageConnection(
                storage_id=storage_id,
                name=payload.name,
                protocol=payload.protocol,
                host=payload.host,
                port=payload.port,
                username=payload.username,
                password_encrypted=encrypt_secret(payload.password),
                base_path=payload.base_path,
                is_shared=payload.is_shared,
                is_active=payload.is_active,
                created_by=actor.id,
            )
        )
        record_audit(
            self.db,
            actor.id,
            "storage.create",
            "storage",
            connection.storage_id,
            connection.name,
            audit_detail(connection.name, meta=_connection_snapshot(connection)),
        )
        self.db.commit()
        return self._with_creator_username(connection, actor.username)

    def update(self, actor: User, connection_id: int, payload: StorageConnectionPayload) -> StorageConnectionItem:
        connection = self._get(connection_id)
        self._ensure_can_manage(actor, connection)
        before = _connection_snapshot(connection)
        connection.name = payload.name
        connection.protocol = payload.protocol
        connection.host = payload.host
        connection.port = payload.port
        connection.username = payload.username
        connection.base_path = payload.base_path
        connection.is_shared = payload.is_shared
        connection.is_active = payload.is_active
        if payload.password:
            connection.password_encrypted = encrypt_secret(payload.password)
        record_audit(
            self.db,
            actor.id,
            "storage.update",
            "storage",
            connection.storage_id,
            connection.name,
            audit_detail(connection.name, audit_changes(before, _connection_snapshot(connection))),
        )
        self.db.commit()
        creator_name = actor.username if connection.created_by == actor.id else self._creator_username(connection)
        return self._with_creator_username(connection, creator_name)

    def delete(self, actor: User, connection_id: int) -> None:
        connection = self._get(connection_id)
        self._ensure_can_manage(actor, connection)
        record_audit(
            self.db,
            actor.id,
            "storage.delete",
            "storage",
            connection.storage_id,
            connection.name,
            audit_detail(connection.name, meta=_connection_snapshot(connection)),
        )
        self.storages.delete(connection)
        self.db.commit()

    def test_connection(self, actor: User, payload: StorageTestRequest) -> None:
        password = payload.password
        if not password and payload.id is not None:
            connection = self._get(payload.id)
            self._ensure_can_manage(actor, connection)
            password = self._password(connection)
        if not password:
            raise bad_request("error.storagePasswordRequired", "Password is required")
        client = self._open_client(payload.protocol, payload.host, payload.port, payload.username, password)
        try:
            if not client.is_dir(payload.base_path):
                raise bad_request("error.storageBasePathMissing", "Base path does not exist")
        finally:
            client.close()

    def list_files(
        self,
        actor: User,
        storage_id: str,
        path: str = "/",
        keyword: str = "",
        recursive: bool = False,
    ) -> StorageFileListResponse:
        connection = self._get_usable(actor, storage_id)
        virtual = _virtual_path(path)
        client = self._connect(connection)
        try:
            if recursive:
                entries, truncated = self._walk(client, connection, virtual, keyword)
            else:
                entries = [
                    _to_entry(virtual, item)
                    for item in client.list_dir(_remote_path(connection, virtual))
                    if _matches(item.name, keyword)
                ]
                truncated = False
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        entries.sort(key=lambda entry: (not entry.is_dir, entry.path.lower()))
        return StorageFileListResponse(path=virtual, entries=entries, truncated=truncated)

    def download(self, actor: User, storage_id: str, path: str) -> tuple[str, Iterator[bytes]]:
        connection = self._get_usable(actor, storage_id)
        virtual = _virtual_path(path)
        if virtual == "/":
            raise bad_request("error.storagePathInvalid", "Invalid path")
        client = self._connect(connection)
        try:
            stream = client.open_download(_remote_path(connection, virtual))
        except StorageOperationError as exc:
            client.close()
            raise _operation_error(exc)
        return posixpath.basename(virtual), _closing_stream(client, stream)

    def upload(self, actor: User, storage_id: str, path: str, filename: str, fileobj: BinaryIO, size: int | None) -> StorageEntry:
        connection = self._get_usable(actor, storage_id)
        directory = _virtual_path(path)
        name = _validated_entry_name(posixpath.basename(filename.replace("\\", "/")))
        virtual = posixpath.join(directory, name)
        client = self._connect(connection)
        try:
            client.upload(_remote_path(connection, virtual), fileobj)
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        meta: dict[str, object] = {"storage_id": connection.storage_id, "path": virtual}
        if size is not None:
            meta["size"] = size
        record_audit(self.db, actor.id, "storage.file_upload", "storage", connection.storage_id, virtual, audit_detail(virtual, meta=meta))
        self.db.commit()
        return StorageEntry(name=name, path=virtual, is_dir=False, size=size or 0)

    def mkdir(self, actor: User, storage_id: str, path: str) -> StorageEntry:
        connection = self._get_usable(actor, storage_id)
        virtual = _virtual_path(path)
        if virtual == "/":
            raise bad_request("error.storagePathInvalid", "Invalid path")
        client = self._connect(connection)
        try:
            client.mkdir(_remote_path(connection, virtual))
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        meta = {"storage_id": connection.storage_id, "path": virtual}
        record_audit(self.db, actor.id, "storage.file_mkdir", "storage", connection.storage_id, virtual, audit_detail(virtual, meta=meta))
        self.db.commit()
        return StorageEntry(name=posixpath.basename(virtual), path=virtual, is_dir=True, size=0)

    def rename(self, actor: User, storage_id: str, path: str, new_name: str) -> StorageEntry:
        connection = self._get_usable(actor, storage_id)
        virtual = _virtual_path(path)
        if virtual == "/":
            raise bad_request("error.storagePathInvalid", "Invalid path")
        name = _validated_entry_name(new_name)
        new_virtual = posixpath.join(posixpath.dirname(virtual), name)
        client = self._connect(connection)
        try:
            client.rename(_remote_path(connection, virtual), _remote_path(connection, new_virtual))
            is_dir = client.is_dir(_remote_path(connection, new_virtual))
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        meta = {"storage_id": connection.storage_id, "path": virtual, "new_path": new_virtual}
        record_audit(self.db, actor.id, "storage.file_rename", "storage", connection.storage_id, virtual, audit_detail(virtual, meta=meta))
        self.db.commit()
        return StorageEntry(name=name, path=new_virtual, is_dir=is_dir, size=0)

    def delete_entry(self, actor: User, storage_id: str, path: str) -> None:
        connection = self._get_usable(actor, storage_id)
        virtual = _virtual_path(path)
        if virtual == "/":
            raise bad_request("error.storagePathInvalid", "Invalid path")
        client = self._connect(connection)
        try:
            remote = _remote_path(connection, virtual)
            is_dir = client.is_dir(remote)
            if is_dir:
                self._delete_recursive(client, remote, depth=0)
            else:
                client.delete_file(remote)
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        meta = {"storage_id": connection.storage_id, "path": virtual, "is_dir": is_dir}
        record_audit(self.db, actor.id, "storage.file_delete", "storage", connection.storage_id, virtual, audit_detail(virtual, meta=meta))
        self.db.commit()

    def _walk(
        self,
        client: StorageClient,
        connection: StorageConnection,
        root: str,
        keyword: str,
    ) -> tuple[list[StorageEntry], bool]:
        entries: list[StorageEntry] = []
        pending = [root]
        scanned_dirs = 0
        while pending:
            if scanned_dirs >= RECURSIVE_MAX_DIRS:
                return entries, True
            current = pending.pop(0)
            scanned_dirs += 1
            for item in client.list_dir(_remote_path(connection, current)):
                child = posixpath.join(current, item.name)
                if item.is_dir and child.count("/") < MAX_TREE_DEPTH:
                    pending.append(child)
                if _matches(item.name, keyword):
                    entries.append(_to_entry(current, item))
                    if len(entries) >= RECURSIVE_MAX_ENTRIES:
                        return entries, True
        return entries, False

    def _delete_recursive(self, client: StorageClient, remote_path: str, depth: int) -> None:
        if depth >= MAX_TREE_DEPTH:
            raise StorageOperationError("Directory tree too deep")
        for item in client.list_dir(remote_path):
            child = posixpath.join(remote_path, item.name)
            if item.is_dir:
                self._delete_recursive(client, child, depth + 1)
            else:
                client.delete_file(child)
        client.delete_empty_dir(remote_path)

    def _get(self, connection_id: int) -> StorageConnection:
        connection = self.storages.get(connection_id)
        if connection is None:
            raise not_found("error.storageNotFound", "Storage connection not found")
        return connection

    def _get_usable(self, actor: User, storage_id: str) -> StorageConnection:
        connection = self.storages.get_by_storage_id(storage_id)
        if connection is None:
            raise not_found("error.storageNotFound", "Storage connection not found")
        if not self._can_use(actor, connection):
            raise forbidden("error.storageUseDenied", "You cannot use this storage connection")
        if not connection.is_active:
            raise bad_request("error.storageDisabled", "Storage connection is disabled")
        return connection

    def _can_use(self, actor: User, connection: StorageConnection) -> bool:
        return (
            connection.created_by == actor.id
            or connection.is_shared
            or has_permission(actor, STORAGE_MANAGE_OTHERS)
        )

    def _ensure_can_manage(self, actor: User, connection: StorageConnection) -> None:
        if connection.created_by == actor.id:
            return
        if has_permission(actor, STORAGE_MANAGE_OTHERS):
            return
        raise forbidden("error.storageManageOthersDenied", "You cannot manage storage connections created by others")

    def _connect(self, connection: StorageConnection) -> StorageClient:
        return self._open_client(
            connection.protocol,
            connection.host,
            connection.port,
            connection.username,
            self._password(connection),
        )

    def _open_client(self, protocol: str, host: str, port: int, username: str, password: str) -> StorageClient:
        try:
            return storage_clients.create_client(protocol, host, port, username, password)
        except StorageConnectError as exc:
            raise service_unavailable("error.storageConnectFailed", "Failed to connect to storage", reason=str(exc))

    def _password(self, connection: StorageConnection) -> str:
        try:
            return decrypt_secret(connection.password_encrypted)
        except ValueError:
            raise bad_request("error.storageCredentialInvalid", "Stored credential cannot be decrypted")

    def _generate_storage_id(self) -> str:
        while True:
            candidate = f"{GENERATED_ID_PREFIX}{secrets.token_hex(5)}"
            if self.storages.get_by_storage_id(candidate) is None:
                return candidate

    def _with_creator_usernames(self, connections: list[StorageConnection]) -> list[StorageConnectionItem]:
        user_ids = {connection.created_by for connection in connections if connection.created_by is not None}
        usernames = self.storages.creator_usernames(user_ids)
        return [
            self._with_creator_username(connection, usernames.get(connection.created_by, ""))
            for connection in connections
        ]

    def _with_creator_username(self, connection: StorageConnection, username: str) -> StorageConnectionItem:
        return StorageConnectionItem.model_validate(connection).model_copy(update={"created_by_username": username})

    def _creator_username(self, connection: StorageConnection) -> str:
        if connection.created_by is None:
            return ""
        return self.storages.creator_usernames({connection.created_by}).get(connection.created_by, "")


def _connection_snapshot(connection: StorageConnection) -> dict[str, object]:
    return {
        "storage_id": connection.storage_id,
        "name": connection.name,
        "protocol": connection.protocol,
        "host": connection.host,
        "port": connection.port,
        "username": connection.username,
        "base_path": connection.base_path,
        "is_shared": connection.is_shared,
        "is_active": connection.is_active,
    }


def _virtual_path(path: str) -> str:
    cleaned = (path or "/").replace("\\", "/")
    depth = 0
    for segment in cleaned.split("/"):
        if segment in ("", "."):
            continue
        depth = depth - 1 if segment == ".." else depth + 1
        if depth < 0:
            raise bad_request("error.storagePathInvalid", "Invalid path")
    normalized = posixpath.normpath("/" + cleaned.strip("/"))
    return "/" if normalized == "/" else normalized


def _remote_path(connection: StorageConnection, virtual: str) -> str:
    base = connection.base_path or "/"
    if virtual == "/":
        return base
    return posixpath.normpath(posixpath.join(base, virtual.lstrip("/")))


def _validated_entry_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or cleaned in (".", "..") or any(char in cleaned for char in ENTRY_NAME_INVALID_CHARS) or len(cleaned) > 255:
        raise bad_request("error.storageNameInvalid", "Invalid file or directory name")
    return cleaned


def _to_entry(parent: str, item: storage_clients.RemoteEntry) -> StorageEntry:
    return StorageEntry(
        name=item.name,
        path=posixpath.join(parent, item.name),
        is_dir=item.is_dir,
        size=item.size,
        modified_at=item.modified_at,
    )


def _matches(name: str, keyword: str) -> bool:
    return keyword.lower() in name.lower() if keyword else True


def _operation_error(exc: StorageOperationError):
    return bad_request("error.storageOperationFailed", "Storage operation failed", reason=str(exc))


def _closing_stream(client: StorageClient, stream: Iterator[bytes]) -> Iterator[bytes]:
    try:
        yield from stream
    finally:
        client.close()
