from __future__ import annotations

import posixpath
import secrets
import tempfile
from collections.abc import Iterator
from typing import BinaryIO

from sqlalchemy.orm import Session
from zipstream import ZIP_DEFLATED, ZipStream

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
    StorageConflictPolicy,
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
        shared: str = "",
        is_active: bool | None = None,
        created_by: str = "",
        sort_order: str = "descend",
        page: int = 1,
        page_size: int = 20,
    ) -> StorageConnectionListResponse:
        visible_to = None if has_permission(actor, STORAGE_MANAGE_OTHERS) else actor.id
        is_shared = {"shared": True, "private": False}.get(shared)
        created_by_user_id = actor.id if created_by == "me" else None
        created_at_order = "ascend" if sort_order == "ascend" else "descend"
        rows, total = self.storages.list(
            keyword,
            protocol,
            is_shared,
            is_active,
            created_by_user_id,
            visible_to,
            created_at_order,
            page,
            page_size,
        )
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

    def check_connection(self, actor: User, storage_id: str) -> None:
        connection = self._get_usable(actor, storage_id)
        client = self._connect(connection)
        try:
            if not client.is_dir(connection.base_path or "/"):
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

    def download_archive(self, actor: User, storage_id: str, path: str) -> tuple[str, Iterator[bytes]]:
        connection = self._get_usable(actor, storage_id)
        virtual = _virtual_path(path)
        client = self._connect(connection)
        stream_ready = False
        try:
            if not client.is_dir(_remote_path(connection, virtual)):
                raise bad_request("error.storageNotDirectory", "Target is not a directory")
            base_name = posixpath.basename(virtual) or connection.storage_id
            archive = ZipStream(compress_type=ZIP_DEFLATED)
            self._add_dir_to_zip(client, connection, virtual, base_name, archive, depth=0)
            stream_ready = True
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            if not stream_ready:
                client.close()
        return f"{base_name}.zip", _zip_stream(archive, client)

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

    def copy_entries(
        self,
        actor: User,
        storage_id: str,
        paths: list[str],
        target_dir: str,
        conflict_policy: StorageConflictPolicy,
    ) -> list[StorageEntry]:
        connection = self._get_usable(actor, storage_id)
        sources = _operation_paths(paths)
        target = _virtual_path(target_dir)
        client = self._connect(connection)
        results: list[StorageEntry] = []
        try:
            self._ensure_remote_dir(client, connection, target)
            for source in sources:
                source_is_dir = self._source_is_dir(client, connection, source)
                _ensure_not_nested(source, target, source_is_dir)
                destination = self._resolve_destination(client, connection, source, target, conflict_policy, delete_existing=True)
                if destination != source:
                    self._copy_entry(client, connection, source, destination, source_is_dir, depth=0)
                results.append(_entry_from_virtual(client, connection, destination))
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        meta = {
            "storage_id": connection.storage_id,
            "paths": sources,
            "target_dir": target,
            "conflict_policy": conflict_policy,
            "results": [entry.path for entry in results],
            "count": len(results),
        }
        record_audit(self.db, actor.id, "storage.file_copy", "storage", connection.storage_id, target, audit_detail(target, meta=meta))
        self.db.commit()
        return results

    def move_entries(
        self,
        actor: User,
        storage_id: str,
        paths: list[str],
        target_dir: str,
        conflict_policy: StorageConflictPolicy,
    ) -> list[StorageEntry]:
        connection = self._get_usable(actor, storage_id)
        sources = _operation_paths(paths)
        target = _virtual_path(target_dir)
        client = self._connect(connection)
        results: list[StorageEntry] = []
        try:
            self._ensure_remote_dir(client, connection, target)
            for source in sources:
                source_is_dir = self._source_is_dir(client, connection, source)
                _ensure_not_nested(source, target, source_is_dir)
                destination = self._resolve_destination(client, connection, source, target, conflict_policy, delete_existing=True)
                if destination != source:
                    client.rename(_remote_path(connection, source), _remote_path(connection, destination))
                results.append(_entry_from_virtual(client, connection, destination))
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        meta = {
            "storage_id": connection.storage_id,
            "paths": sources,
            "target_dir": target,
            "conflict_policy": conflict_policy,
            "results": [entry.path for entry in results],
            "count": len(results),
        }
        record_audit(self.db, actor.id, "storage.file_move", "storage", connection.storage_id, target, audit_detail(target, meta=meta))
        self.db.commit()
        return results

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

    def delete_entries(self, actor: User, storage_id: str, paths: list[str]) -> int:
        connection = self._get_usable(actor, storage_id)
        sources = _operation_paths(paths)
        client = self._connect(connection)
        deleted: list[dict[str, object]] = []
        try:
            for source in sources:
                remote = _remote_path(connection, source)
                is_dir = self._source_is_dir(client, connection, source)
                if is_dir:
                    self._delete_recursive(client, remote, depth=0)
                else:
                    client.delete_file(remote)
                deleted.append({"path": source, "is_dir": is_dir})
        except StorageOperationError as exc:
            raise _operation_error(exc)
        finally:
            client.close()
        meta = {"storage_id": connection.storage_id, "entries": deleted, "count": len(deleted)}
        record_audit(
            self.db,
            actor.id,
            "storage.file_batch_delete",
            "storage",
            connection.storage_id,
            connection.storage_id,
            audit_detail(connection.storage_id, meta=meta),
        )
        self.db.commit()
        return len(deleted)

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

    def _add_dir_to_zip(
        self,
        client: StorageClient,
        connection: StorageConnection,
        virtual_dir: str,
        arc_prefix: str,
        archive: ZipStream,
        depth: int,
    ) -> None:
        if depth >= MAX_TREE_DEPTH:
            raise StorageOperationError("Directory tree too deep")
        items = client.list_dir(_remote_path(connection, virtual_dir))
        if not items:
            archive.mkdir(arc_prefix)
            return
        for item in items:
            child_virtual = posixpath.join(virtual_dir, item.name)
            arcname = f"{arc_prefix}/{item.name}"
            if item.is_dir:
                self._add_dir_to_zip(client, connection, child_virtual, arcname, archive, depth + 1)
            else:
                remote = _remote_path(connection, child_virtual)
                archive.add(_lazy_download(client, remote), arcname=arcname)

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

    def _ensure_remote_dir(self, client: StorageClient, connection: StorageConnection, virtual: str) -> None:
        if not client.is_dir(_remote_path(connection, virtual)):
            raise bad_request("error.storageNotDirectory", "Target is not a directory")

    def _source_is_dir(self, client: StorageClient, connection: StorageConnection, virtual: str) -> bool:
        if virtual == "/" or not _entry_exists(client, connection, virtual):
            raise StorageOperationError("No such entry")
        return client.is_dir(_remote_path(connection, virtual))

    def _resolve_destination(
        self,
        client: StorageClient,
        connection: StorageConnection,
        source: str,
        target_dir: str,
        conflict_policy: StorageConflictPolicy,
        delete_existing: bool,
    ) -> str:
        destination = posixpath.join(target_dir, posixpath.basename(source))
        if not _entry_exists(client, connection, destination):
            return destination
        if conflict_policy == "rename":
            return _unique_destination(client, connection, target_dir, posixpath.basename(source))
        if conflict_policy == "overwrite":
            if destination != source and delete_existing:
                self._delete_virtual(client, connection, destination)
            return destination
        raise bad_request("error.storageTargetExists", "Target already exists")

    def _delete_virtual(self, client: StorageClient, connection: StorageConnection, virtual: str) -> None:
        if virtual == "/":
            raise bad_request("error.storagePathInvalid", "Invalid path")
        remote = _remote_path(connection, virtual)
        if client.is_dir(remote):
            self._delete_recursive(client, remote, depth=0)
        else:
            client.delete_file(remote)

    def _copy_entry(
        self,
        client: StorageClient,
        connection: StorageConnection,
        source: str,
        destination: str,
        source_is_dir: bool,
        depth: int,
    ) -> None:
        if depth >= MAX_TREE_DEPTH:
            raise StorageOperationError("Directory tree too deep")
        source_remote = _remote_path(connection, source)
        destination_remote = _remote_path(connection, destination)
        if source_is_dir:
            client.mkdir(destination_remote)
            for item in client.list_dir(source_remote):
                child_source = posixpath.join(source, item.name)
                child_destination = posixpath.join(destination, item.name)
                self._copy_entry(client, connection, child_source, child_destination, item.is_dir, depth + 1)
            return
        with tempfile.SpooledTemporaryFile(max_size=8 * 1024 * 1024) as buffer:
            for chunk in client.open_download(source_remote):
                buffer.write(chunk)
            buffer.seek(0)
            client.upload(destination_remote, buffer)

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


def _operation_paths(paths: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for path in paths:
        virtual = _virtual_path(path)
        if virtual == "/" or virtual in seen:
            continue
        seen.add(virtual)
        result.append(virtual)
    if not result:
        raise bad_request("error.storagePathInvalid", "Invalid path")
    return result


def _entry_exists(client: StorageClient, connection: StorageConnection, virtual: str) -> bool:
    if virtual == "/":
        return True
    parent = posixpath.dirname(virtual) or "/"
    name = posixpath.basename(virtual)
    try:
        return any(item.name == name for item in client.list_dir(_remote_path(connection, parent)))
    except StorageOperationError:
        return False


def _unique_destination(client: StorageClient, connection: StorageConnection, target_dir: str, name: str) -> str:
    existing = {item.name for item in client.list_dir(_remote_path(connection, target_dir))}
    stem, suffix = _split_name(name)
    candidate = f"{stem} - copy{suffix}"
    index = 2
    while candidate in existing:
        candidate = f"{stem} - copy {index}{suffix}"
        index += 1
    return posixpath.join(target_dir, candidate)


def _split_name(name: str) -> tuple[str, str]:
    stem, suffix = posixpath.splitext(name)
    return (stem or name, suffix if stem else "")


def _entry_from_virtual(client: StorageClient, connection: StorageConnection, virtual: str) -> StorageEntry:
    parent = posixpath.dirname(virtual) or "/"
    name = posixpath.basename(virtual)
    for item in client.list_dir(_remote_path(connection, parent)):
        if item.name == name:
            return _to_entry(parent, item)
    return StorageEntry(name=name, path=virtual, is_dir=client.is_dir(_remote_path(connection, virtual)), size=0)


def _ensure_not_nested(source: str, target_dir: str, source_is_dir: bool) -> None:
    if source_is_dir and (target_dir == source or target_dir.startswith(source.rstrip("/") + "/")):
        raise bad_request("error.storagePathInvalid", "Invalid path")


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


def _lazy_download(client: StorageClient, remote_path: str) -> Iterator[bytes]:
    yield from client.open_download(remote_path)


def _zip_stream(archive: ZipStream, client: StorageClient) -> Iterator[bytes]:
    try:
        yield from archive
    finally:
        client.close()
