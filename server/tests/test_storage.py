import io
import posixpath

from sqlalchemy import create_engine, text

from app.modules.storage.clients import RemoteEntry, StorageConnectError, StorageOperationError
from test_auth_rbac import create_client, install_sqlite, login, page_items

STORAGE_BASE_CODES = {
    "route:storage",
    "action:storage:create",
    "action:storage:read",
    "action:storage:update",
    "action:storage:delete",
    "action:storage:operate",
}


class FakeRemoteFS:
    def __init__(self):
        self.dirs = {"/", "/data", "/data/docs"}
        self.files = {"/data/a.txt": b"hello", "/data/docs/b.log": b"log-content"}


class FakeStorageClient:
    def __init__(self, fs: FakeRemoteFS, record: dict):
        self.fs = fs
        self.record = record
        self.closed = False

    def list_dir(self, path):
        if path not in self.fs.dirs:
            raise StorageOperationError(f"No such directory: {path}")
        prefix = path.rstrip("/") + "/"
        entries = []
        for directory in self.fs.dirs:
            if directory != path and directory.startswith(prefix) and "/" not in directory[len(prefix):]:
                entries.append(RemoteEntry(name=directory[len(prefix):], is_dir=True, size=0, modified_at=""))
        for file_path, data in self.fs.files.items():
            if file_path.startswith(prefix) and "/" not in file_path[len(prefix):]:
                entries.append(
                    RemoteEntry(
                        name=file_path[len(prefix):],
                        is_dir=False,
                        size=len(data),
                        modified_at="2026-06-12T00:00:00+00:00",
                    )
                )
        return entries

    def is_dir(self, path):
        return path in self.fs.dirs

    def open_download(self, path):
        if path not in self.fs.files:
            raise StorageOperationError(f"No such file: {path}")
        data = self.fs.files[path]

        def stream():
            yield data

        return stream()

    def upload(self, path, fileobj):
        if posixpath.dirname(path) not in self.fs.dirs:
            raise StorageOperationError("No such directory")
        self.fs.files[path] = fileobj.read()

    def delete_file(self, path):
        if path not in self.fs.files:
            raise StorageOperationError(f"No such file: {path}")
        del self.fs.files[path]

    def delete_empty_dir(self, path):
        prefix = path.rstrip("/") + "/"
        if any(d.startswith(prefix) for d in self.fs.dirs) or any(f.startswith(prefix) for f in self.fs.files):
            raise StorageOperationError("Directory not empty")
        self.fs.dirs.discard(path)

    def mkdir(self, path):
        if posixpath.dirname(path) not in self.fs.dirs:
            raise StorageOperationError("No such directory")
        if path in self.fs.dirs:
            raise StorageOperationError("Directory exists")
        self.fs.dirs.add(path)

    def rename(self, old_path, new_path):
        if old_path in self.fs.files:
            self.fs.files[new_path] = self.fs.files.pop(old_path)
            return
        if old_path in self.fs.dirs:
            for directory in sorted(d for d in self.fs.dirs if d == old_path or d.startswith(old_path + "/")):
                self.fs.dirs.discard(directory)
                self.fs.dirs.add(new_path + directory[len(old_path):])
            for file_path in sorted(f for f in self.fs.files if f.startswith(old_path + "/")):
                self.fs.files[new_path + file_path[len(old_path):]] = self.fs.files.pop(file_path)
            return
        raise StorageOperationError("No such entry")

    def close(self):
        self.closed = True


def install_fake_clients(monkeypatch, fs: FakeRemoteFS):
    created = []

    def factory(protocol, host, port, username, password):
        record = {"protocol": protocol, "host": host, "port": port, "username": username, "password": password}
        client = FakeStorageClient(fs, record)
        created.append(client)
        return client

    monkeypatch.setattr("app.modules.storage.clients.create_client", factory)
    return created


def storage_payload(**overrides):
    payload = {
        "name": "测试储存",
        "storage_id": "",
        "protocol": "ftp",
        "host": "10.0.0.8",
        "port": 21,
        "username": "ftpuser",
        "password": "FtpPass123",
        "base_path": "/data",
        "is_shared": False,
        "is_active": True,
    }
    payload.update(overrides)
    return payload


def grant_storage_role(client, admin_headers, code, permission_codes):
    permissions = client.get("/api/permissions", headers=admin_headers).json()
    permission_ids_by_code = {item["code"]: item["id"] for item in permissions}
    role = client.post("/api/roles", json={"code": code, "name": code, "description": ""}, headers=admin_headers)
    assert role.status_code == 200
    role_id = role.json()["id"]
    assign = client.put(
        f"/api/roles/{role_id}/permissions",
        json={"permission_ids": [permission_ids_by_code[item] for item in permission_codes]},
        headers=admin_headers,
    )
    assert assign.status_code == 200
    return role_id, permission_ids_by_code


def create_storage_user(client, admin_headers, username, role_id):
    user = client.post(
        "/api/users",
        json={
            "username": username,
            "password": "Storage123",
            "full_name": username,
            "phone": "13800000031",
            "email": f"{username}@example.com",
            "company": "",
            "department": "",
            "role_ids": [role_id],
        },
        headers=admin_headers,
    )
    assert user.status_code == 200
    return login(client, username, "Storage123")


def test_storage_connection_crud_and_id_rules(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    custom = client.post("/api/storages", json=storage_payload(storage_id="my-storage_01"), headers=admin_headers)
    assert custom.status_code == 200
    assert custom.json()["storage_id"] == "my-storage_01"
    assert "password" not in custom.json()
    assert "password_encrypted" not in custom.json()

    duplicate = client.post("/api/storages", json=storage_payload(storage_id="my-storage_01"), headers=admin_headers)
    assert duplicate.status_code == 400
    assert duplicate.json()["detail"]["code"] == "error.storageIdTaken"

    missing_password = client.post("/api/storages", json=storage_payload(password=""), headers=admin_headers)
    assert missing_password.status_code == 400
    assert missing_password.json()["detail"]["code"] == "error.storagePasswordRequired"

    assert client.post("/api/storages", json=storage_payload(storage_id="ab"), headers=admin_headers).status_code == 422
    assert client.post("/api/storages", json=storage_payload(protocol="webdav"), headers=admin_headers).status_code == 422
    assert client.post("/api/storages", json=storage_payload(base_path="/a/../../b"), headers=admin_headers).status_code == 422

    generated = client.post("/api/storages", json=storage_payload(storage_id="", name="自动 ID"), headers=admin_headers)
    assert generated.status_code == 200
    generated_item = generated.json()
    assert generated_item["storage_id"].startswith("stg_")

    from app.core.install import load_install_config
    from app.core.security import decrypt_secret

    engine = create_engine(load_install_config().database_url)
    with engine.connect() as conn:
        encrypted = conn.execute(
            text("SELECT password_encrypted FROM storage_connections WHERE storage_id = 'my-storage_01'")
        ).scalar_one()
    engine.dispose()
    assert encrypted != "FtpPass123"
    assert decrypt_secret(encrypted) == "FtpPass123"

    updated = client.put(
        f"/api/storages/{custom.json()['id']}",
        json=storage_payload(storage_id="ignored-by-update", name="改名", password="", is_shared=True),
        headers=admin_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "改名"
    assert updated.json()["storage_id"] == "my-storage_01"
    assert updated.json()["is_shared"] is True

    engine = create_engine(load_install_config().database_url)
    with engine.connect() as conn:
        unchanged = conn.execute(
            text("SELECT password_encrypted FROM storage_connections WHERE storage_id = 'my-storage_01'")
        ).scalar_one()
    engine.dispose()
    assert decrypt_secret(unchanged) == "FtpPass123"

    filtered_shared = client.get("/api/storages", params={"shared": "shared"}, headers=admin_headers)
    assert [item["storage_id"] for item in page_items(filtered_shared)] == ["my-storage_01"]
    filtered_private = client.get("/api/storages", params={"shared": "private"}, headers=admin_headers)
    assert [item["storage_id"] for item in page_items(filtered_private)] == [generated_item["storage_id"]]
    filtered_protocol = client.get("/api/storages", params={"protocol": "sftp"}, headers=admin_headers)
    assert page_items(filtered_protocol) == []
    ascending = client.get("/api/storages", params={"sort_order": "ascend"}, headers=admin_headers)
    assert [item["storage_id"] for item in page_items(ascending)] == ["my-storage_01", generated_item["storage_id"]]
    only_mine = client.get("/api/storages", params={"created_by": "me"}, headers=admin_headers)
    assert len(page_items(only_mine)) == 2

    deleted = client.delete(f"/api/storages/{generated_item['id']}", headers=admin_headers)
    assert deleted.status_code == 200
    remaining = client.get("/api/storages", headers=admin_headers)
    assert [item["storage_id"] for item in page_items(remaining)] == ["my-storage_01"]

    logs = client.get(
        "/api/audit-logs",
        params={"actor_scope": "all", "target_type": "storage", "page_size": 100},
        headers=admin_headers,
    )
    actions = {item["action"] for item in page_items(logs)}
    assert {"storage.create", "storage.update", "storage.delete"}.issubset(actions)
    for item in page_items(logs):
        assert "FtpPass123" not in (item["detail_data"] and str(item["detail_data"]) or "")


def test_storage_share_scope_and_manage_rules(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    fs = FakeRemoteFS()
    install_fake_clients(monkeypatch, fs)

    private = client.post(
        "/api/storages", json=storage_payload(storage_id="admin-private", name="管理员私有"), headers=admin_headers
    )
    assert private.status_code == 200
    shared = client.post(
        "/api/storages",
        json=storage_payload(storage_id="admin-shared", name="管理员共享", is_shared=True),
        headers=admin_headers,
    )
    assert shared.status_code == 200

    role_id, permission_ids_by_code = grant_storage_role(client, admin_headers, "storage_user", STORAGE_BASE_CODES)
    user_headers = create_storage_user(client, admin_headers, "storage_u1", role_id)

    visible = client.get("/api/storages", headers=user_headers)
    assert visible.status_code == 200
    assert [item["storage_id"] for item in page_items(visible)] == ["admin-shared"]

    own = client.post(
        "/api/storages", json=storage_payload(storage_id="u1-own", name="自己的"), headers=user_headers
    )
    assert own.status_code == 200
    mine = client.get("/api/storages", headers=user_headers)
    assert {item["storage_id"] for item in page_items(mine)} == {"admin-shared", "u1-own"}

    edit_shared = client.put(
        f"/api/storages/{shared.json()['id']}",
        json=storage_payload(name="越权改名", is_shared=True),
        headers=user_headers,
    )
    assert edit_shared.status_code == 403
    assert edit_shared.json()["detail"]["code"] == "error.storageManageOthersDenied"
    assert client.delete(f"/api/storages/{shared.json()['id']}", headers=user_headers).status_code == 403

    private_files = client.get("/api/storages/admin-private/files", headers=user_headers)
    assert private_files.status_code == 403
    assert private_files.json()["detail"]["code"] == "error.storageUseDenied"

    shared_files = client.get("/api/storages/admin-shared/files", headers=user_headers)
    assert shared_files.status_code == 200
    assert {entry["name"] for entry in shared_files.json()["entries"]} == {"docs", "a.txt"}

    upgraded = client.put(
        f"/api/roles/{role_id}/permissions",
        json={
            "permission_ids": [
                permission_ids_by_code[code]
                for code in {*STORAGE_BASE_CODES, "action:storage:manage_others"}
            ]
        },
        headers=admin_headers,
    )
    assert upgraded.status_code == 200

    all_visible = client.get("/api/storages", headers=user_headers)
    assert {item["storage_id"] for item in page_items(all_visible)} == {"admin-private", "admin-shared", "u1-own"}
    allowed_edit = client.put(
        f"/api/storages/{shared.json()['id']}",
        json=storage_payload(name="管理他人", is_shared=True),
        headers=user_headers,
    )
    assert allowed_edit.status_code == 200
    assert client.get("/api/storages/admin-private/files", headers=user_headers).status_code == 200


def test_storage_file_operations_with_fake_client(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    fs = FakeRemoteFS()
    created_clients = install_fake_clients(monkeypatch, fs)

    storage = client.post("/api/storages", json=storage_payload(storage_id="files-demo"), headers=admin_headers)
    assert storage.status_code == 200

    listing = client.get("/api/storages/files-demo/files", headers=admin_headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["path"] == "/"
    assert [entry["name"] for entry in body["entries"]] == ["docs", "a.txt"]
    assert body["entries"][0]["is_dir"] is True
    assert created_clients[-1].record["password"] == "FtpPass123"
    assert all(instance.closed for instance in created_clients)

    filtered = client.get("/api/storages/files-demo/files", params={"keyword": "a.t"}, headers=admin_headers)
    assert [entry["name"] for entry in filtered.json()["entries"]] == ["a.txt"]

    searched = client.get(
        "/api/storages/files-demo/files", params={"keyword": "b.log", "recursive": True}, headers=admin_headers
    )
    assert searched.status_code == 200
    assert [entry["path"] for entry in searched.json()["entries"]] == ["/docs/b.log"]

    escape = client.get("/api/storages/files-demo/files", params={"path": "../etc"}, headers=admin_headers)
    assert escape.status_code == 400
    assert escape.json()["detail"]["code"] == "error.storagePathInvalid"

    uploaded = client.post(
        "/api/storages/files-demo/upload",
        params={"path": "/docs"},
        files={"file": ("new.bin", io.BytesIO(b"binary-data"), "application/octet-stream")},
        headers=admin_headers,
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["path"] == "/docs/new.bin"
    assert fs.files["/data/docs/new.bin"] == b"binary-data"

    downloaded = client.get("/api/storages/files-demo/download", params={"path": "/a.txt"}, headers=admin_headers)
    assert downloaded.status_code == 200
    assert downloaded.content == b"hello"
    assert "attachment" in downloaded.headers["content-disposition"]

    missing = client.get("/api/storages/files-demo/download", params={"path": "/nope.txt"}, headers=admin_headers)
    assert missing.status_code == 400
    assert missing.json()["detail"]["code"] == "error.storageOperationFailed"

    mkdir = client.post("/api/storages/files-demo/mkdir", json={"path": "/docs/sub"}, headers=admin_headers)
    assert mkdir.status_code == 200
    assert "/data/docs/sub" in fs.dirs

    renamed = client.post(
        "/api/storages/files-demo/rename", json={"path": "/a.txt", "new_name": "a2.txt"}, headers=admin_headers
    )
    assert renamed.status_code == 200
    assert renamed.json()["path"] == "/a2.txt"
    assert "/data/a2.txt" in fs.files and "/data/a.txt" not in fs.files

    bad_name = client.post(
        "/api/storages/files-demo/rename", json={"path": "/a2.txt", "new_name": "x/y"}, headers=admin_headers
    )
    assert bad_name.status_code == 422

    removed_dir = client.delete("/api/storages/files-demo/files", params={"path": "/docs"}, headers=admin_headers)
    assert removed_dir.status_code == 200
    assert "/data/docs" not in fs.dirs
    assert all(not name.startswith("/data/docs/") for name in fs.files)

    disabled = client.put(
        f"/api/storages/{storage.json()['id']}",
        json=storage_payload(is_active=False),
        headers=admin_headers,
    )
    assert disabled.status_code == 200
    blocked = client.get("/api/storages/files-demo/files", headers=admin_headers)
    assert blocked.status_code == 400
    assert blocked.json()["detail"]["code"] == "error.storageDisabled"

    logs = client.get(
        "/api/audit-logs",
        params={"actor_scope": "all", "target_type": "storage", "page_size": 100},
        headers=admin_headers,
    )
    actions = {item["action"] for item in page_items(logs)}
    assert {"storage.file_upload", "storage.file_mkdir", "storage.file_rename", "storage.file_delete"}.issubset(actions)


def test_storage_test_endpoint_and_connect_failure(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    fs = FakeRemoteFS()
    created_clients = install_fake_clients(monkeypatch, fs)

    direct = client.post(
        "/api/storages/test",
        json={"protocol": "ftp", "host": "10.0.0.8", "port": 21, "username": "ftpuser", "password": "FtpPass123", "base_path": "/data"},
        headers=admin_headers,
    )
    assert direct.status_code == 200
    assert direct.json()["code"] == "storage.connectionOk"

    missing_base = client.post(
        "/api/storages/test",
        json={"protocol": "ftp", "host": "10.0.0.8", "port": 21, "username": "ftpuser", "password": "FtpPass123", "base_path": "/missing"},
        headers=admin_headers,
    )
    assert missing_base.status_code == 400
    assert missing_base.json()["detail"]["code"] == "error.storageBasePathMissing"

    storage = client.post("/api/storages", json=storage_payload(storage_id="test-reuse"), headers=admin_headers)
    assert storage.status_code == 200
    reused = client.post(
        "/api/storages/test",
        json={
            "id": storage.json()["id"],
            "protocol": "ftp",
            "host": "10.0.0.8",
            "port": 21,
            "username": "ftpuser",
            "password": "",
            "base_path": "/data",
        },
        headers=admin_headers,
    )
    assert reused.status_code == 200
    assert created_clients[-1].record["password"] == "FtpPass123"

    def failing_factory(protocol, host, port, username, password):
        raise StorageConnectError("connection refused")

    monkeypatch.setattr("app.modules.storage.clients.create_client", failing_factory)
    failed = client.get("/api/storages/test-reuse/files", headers=admin_headers)
    assert failed.status_code == 503
    assert failed.json()["detail"]["code"] == "error.storageConnectFailed"
    assert failed.json()["detail"]["params"]["reason"] == "connection refused"


def test_storage_api_token_access_and_openapi_visibility(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    fs = FakeRemoteFS()
    install_fake_clients(monkeypatch, fs)

    storage = client.post(
        "/api/storages", json=storage_payload(storage_id="api-shared", is_shared=True), headers=admin_headers
    )
    assert storage.status_code == 200

    token = client.post("/api/tokens", json={"name": "外部集成", "expires_at": None}, headers=admin_headers)
    assert token.status_code == 200
    api_headers = {"Authorization": f"Bearer {token.json()['token']}"}

    api_listing = client.get("/api/storages/api-shared/files", headers=api_headers)
    assert api_listing.status_code == 200
    assert {entry["name"] for entry in api_listing.json()["entries"]} == {"docs", "a.txt"}

    api_upload = client.post(
        "/api/storages/api-shared/upload",
        params={"path": "/"},
        files={"file": ("token.txt", io.BytesIO(b"from-token"), "text/plain")},
        headers=api_headers,
    )
    assert api_upload.status_code == 200
    assert fs.files["/data/token.txt"] == b"from-token"

    manage_via_token = client.get("/api/storages", headers=api_headers)
    assert manage_via_token.status_code == 403
    assert manage_via_token.json()["detail"]["code"] == "error.webOnly"

    openapi = client.get("/openapi.json", headers=admin_headers)
    assert openapi.status_code == 200
    schema = openapi.json()
    paths = schema["paths"]
    assert "/api/storages/{storage_id}/files" in paths
    assert "/api/storages/{storage_id}/upload" in paths
    assert "/api/storages" not in paths
    assert "/api/storages/test" not in paths
    assert "/api/storages/{connection_id}" not in paths
    visible_tags = {
        tag
        for path_item in paths.values()
        for operation in path_item.values()
        if isinstance(operation, dict)
        for tag in operation.get("tags", [])
    }
    assert "storage-files" in visible_tags
    assert "storages" not in visible_tags


def test_storage_parallel_connections_use_isolated_clients(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    fs = FakeRemoteFS()
    created_clients = install_fake_clients(monkeypatch, fs)

    first = client.post(
        "/api/storages",
        json=storage_payload(storage_id="conn-a", host="10.0.0.8", username="user_a"),
        headers=admin_headers,
    )
    second = client.post(
        "/api/storages",
        json=storage_payload(storage_id="conn-b", host="10.0.0.9", username="user_b", protocol="sftp", port=22),
        headers=admin_headers,
    )
    assert first.status_code == 200
    assert second.status_code == 200

    for _ in range(2):
        assert client.get("/api/storages/conn-a/files", headers=admin_headers).status_code == 200
        assert client.get("/api/storages/conn-b/files", headers=admin_headers).status_code == 200

    assert len(created_clients) == 4
    assert [instance.record["host"] for instance in created_clients] == ["10.0.0.8", "10.0.0.9", "10.0.0.8", "10.0.0.9"]
    assert all(instance.closed for instance in created_clients)
    assert created_clients[1].record["protocol"] == "sftp"
