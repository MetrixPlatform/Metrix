import io
import threading
import time
import zipfile

from test_auth_rbac import create_client, install_sqlite, login, page_items

SCRIPT_BASE_CODES = {
    "action:script:create",
    "action:script:read",
    "action:script:update",
    "action:script:delete",
    "action:script:operate",
}


class FakeImage:
    def __init__(self, image_id: str, tags: list[str]):
        self.id = image_id
        self.short_id = image_id.replace("sha256:", "")[:12]
        self.tags = tags
        self.attrs = {
            "Id": image_id,
            "RepoTags": tags,
            "Os": "linux",
            "Architecture": "amd64",
            "Config": {"Labels": {}},
        }


class FakeRunContainer:
    def __init__(self, gate: threading.Event, exit_code: int, labels: dict[str, str]):
        self.gate = gate
        self.exit_code = exit_code
        self.labels = labels
        self.removed = False
        self.killed = False
        self.attrs = {"State": {"ExitCode": exit_code}}

    def logs(self, stream=False, follow=False):
        if stream:
            def generate():
                yield b"script started\n"
                self.gate.wait(timeout=10)
                yield b"script finished\n"

            return generate()
        return b"script started\nscript finished\n"

    def wait(self, timeout=None):
        return {"StatusCode": self.exit_code}

    def reload(self):
        pass

    def kill(self):
        self.killed = True
        self.gate.set()

    def remove(self, force=False):
        self.removed = True
        self.gate.set()


class FakeContainers:
    def __init__(self, engine):
        self.engine = engine
        self.created: list[FakeRunContainer] = []

    def run(self, **kwargs):
        if kwargs.get("detach"):
            gate = threading.Event()
            if not self.engine.hold_runs:
                gate.set()
            container = FakeRunContainer(gate, self.engine.run_exit_code, kwargs.get("labels", {}))
            self.created.append(container)
            self.engine.last_run = kwargs
            return container
        return self.engine.oneshot_output

    def list(self, all=True, filters=None):
        result = [container for container in self.created if not container.removed]
        label = (filters or {}).get("label")
        if label and "=" in label:
            key, value = label.split("=", 1)
            result = [container for container in result if container.labels.get(key) == value]
        return result


class FakeImages:
    def __init__(self, engine):
        self.engine = engine

    def list(self):
        return list(self.engine.image_list)

    def get(self, image_ref):
        for image in self.engine.image_list:
            if image.id == image_ref or image_ref in image.tags:
                return image
        raise KeyError(image_ref)


class FakeScriptDockerEngine:
    def __init__(self):
        self.image_list = [FakeImage("sha256:py", ["python:3.12-slim"])]
        self.containers = FakeContainers(self)
        self.images = FakeImages(self)
        self.hold_runs = False
        self.run_exit_code = 0
        self.oneshot_output = b"Python 3.12.0\n---\npip 24.0\n"
        self.last_run: dict = {}

    def ping(self):
        return True


def install_fake_docker(monkeypatch) -> FakeScriptDockerEngine:
    from app.modules.containers.clients import DockerAdapter

    engine = FakeScriptDockerEngine()
    monkeypatch.setattr(
        "app.modules.containers.clients.create_client",
        lambda config=None: DockerAdapter(engine, "fake://docker"),
    )
    return engine


def project_payload(**overrides):
    payload = {
        "name": "示例脚本",
        "description": "",
        "language": "python",
        "base_image": "python:3.12-slim",
        "network_mode": "bridge",
        "run_command": "python main.py",
        "env": {},
        "cpu_limit": None,
        "memory_limit_mb": None,
        "timeout_seconds": 600,
    }
    payload.update(overrides)
    return payload


def grant_script_role(client, admin_headers, code, permission_codes):
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


def create_script_user(client, admin_headers, username, role_id, phone):
    user = client.post(
        "/api/users",
        json={
            "username": username,
            "password": "Script123",
            "full_name": username,
            "phone": phone,
            "email": f"{username}@example.com",
            "company": "",
            "department": "",
            "role_ids": [role_id],
        },
        headers=admin_headers,
    )
    assert user.status_code == 200
    return login(client, username, "Script123")


def wait_run(client, headers, run_id, statuses, attempts=80):
    for _ in range(attempts):
        response = client.get(f"/api/scripts/runs/{run_id}", headers=headers)
        if response.status_code == 200 and response.json()["status"] in statuses:
            return response.json()
        time.sleep(0.05)
    raise AssertionError(f"run {run_id} did not reach {statuses}")


def test_script_project_crud_and_owner_scope(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    created = client.post("/api/scripts", json=project_payload(name="管理员脚本"), headers=admin_headers)
    assert created.status_code == 200
    admin_project = created.json()
    assert admin_project["slug"].startswith("scr_")
    assert admin_project["workspace_path"].startswith("script_workspaces/")
    assert admin_project["network_mode"] == "bridge"

    role_id, permission_ids_by_code = grant_script_role(client, admin_headers, "script_user", SCRIPT_BASE_CODES)
    user_headers = create_script_user(client, admin_headers, "script_u1", role_id, "13800000051")

    own = client.post("/api/scripts", json=project_payload(name="用户脚本"), headers=user_headers)
    assert own.status_code == 200
    user_project = own.json()

    visible = client.get("/api/scripts", headers=user_headers)
    assert [item["id"] for item in page_items(visible)] == [user_project["id"]]

    denied_update = client.put(f"/api/scripts/{admin_project['id']}", json=project_payload(name="越权"), headers=user_headers)
    assert denied_update.status_code == 403
    assert denied_update.json()["detail"]["code"] == "error.scriptManageOthersDenied"
    assert client.delete(f"/api/scripts/{admin_project['id']}", headers=user_headers).status_code == 403

    own_update = client.put(f"/api/scripts/{user_project['id']}", json=project_payload(name="改名"), headers=user_headers)
    assert own_update.status_code == 200
    assert own_update.json()["name"] == "改名"

    upgraded = client.put(
        f"/api/roles/{role_id}/permissions",
        json={"permission_ids": [permission_ids_by_code[code] for code in {*SCRIPT_BASE_CODES, "action:script:manage_others"}]},
        headers=admin_headers,
    )
    assert upgraded.status_code == 200
    all_visible = client.get("/api/scripts", headers=user_headers)
    assert {item["id"] for item in page_items(all_visible)} == {admin_project["id"], user_project["id"]}
    assert client.put(f"/api/scripts/{admin_project['id']}", json=project_payload(name="管理他人"), headers=user_headers).status_code == 200

    logs = client.get("/api/audit-logs", params={"actor_scope": "all", "target_type": "script_project", "page_size": 100}, headers=admin_headers)
    actions = {item["action"] for item in page_items(logs)}
    assert {"script.create", "script.update"}.issubset(actions)


def test_script_workspace_files_and_path_escape(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    project = client.post("/api/scripts", json=project_payload(), headers=admin_headers).json()
    pid = project["id"]

    empty = client.get(f"/api/scripts/{pid}/files", headers=admin_headers)
    assert empty.status_code == 200
    assert empty.json()["entries"] == []

    write = client.post(f"/api/scripts/{pid}/file", json={"path": "/main.py", "content": "print('hi')\n"}, headers=admin_headers)
    assert write.status_code == 200
    assert write.json()["path"] == "/main.py"

    listing = client.get(f"/api/scripts/{pid}/files", headers=admin_headers)
    assert [entry["name"] for entry in listing.json()["entries"]] == ["main.py"]

    read = client.get(f"/api/scripts/{pid}/file", params={"path": "/main.py"}, headers=admin_headers)
    assert read.status_code == 200
    assert read.json()["content"] == "print('hi')\n"

    mkdir = client.post(f"/api/scripts/{pid}/mkdir", json={"path": "/pkg"}, headers=admin_headers)
    assert mkdir.status_code == 200
    assert mkdir.json()["is_dir"] is True
    assert client.post(f"/api/scripts/{pid}/file", json={"path": "/pkg/util.py", "content": "x = 1\n"}, headers=admin_headers).status_code == 200

    for escape in ("../etc", "/../../secret"):
        blocked = client.get(f"/api/scripts/{pid}/files", params={"path": escape}, headers=admin_headers)
        assert blocked.status_code == 400
        assert blocked.json()["detail"]["code"] == "error.scriptPathInvalid"
    escape_write = client.post(f"/api/scripts/{pid}/file", json={"path": "../evil.py", "content": "bad"}, headers=admin_headers)
    assert escape_write.status_code == 400
    assert escape_write.json()["detail"]["code"] == "error.scriptPathInvalid"

    rename = client.post(f"/api/scripts/{pid}/rename", json={"path": "/main.py", "new_name": "app.py"}, headers=admin_headers)
    assert rename.status_code == 200
    assert rename.json()["path"] == "/app.py"

    upload = client.post(
        f"/api/scripts/{pid}/upload",
        params={"path": "/pkg"},
        files={"file": ("dep.whl", io.BytesIO(b"wheel-bytes"), "application/octet-stream")},
        headers=admin_headers,
    )
    assert upload.status_code == 200
    assert upload.json()["path"] == "/pkg/dep.whl"

    removed = client.delete(f"/api/scripts/{pid}/files", params={"path": "/pkg"}, headers=admin_headers)
    assert removed.status_code == 200
    after = client.get(f"/api/scripts/{pid}/files", headers=admin_headers)
    assert [entry["name"] for entry in after.json()["entries"]] == ["app.py"]


def test_script_workspace_quota_enforced(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    settings = client.get("/api/settings", headers=admin_headers).json()
    settings["script_workspace_quota_mb"] = 1
    assert client.put("/api/settings", json=settings, headers=admin_headers).status_code == 200

    project = client.post("/api/scripts", json=project_payload(), headers=admin_headers).json()
    over_quota = client.post(
        f"/api/scripts/{project['id']}/file",
        json={"path": "/big.txt", "content": "x" * (2 * 1024 * 1024)},
        headers=admin_headers,
    )
    assert over_quota.status_code == 400
    assert over_quota.json()["detail"]["code"] == "error.scriptQuotaExceeded"


def test_script_run_lifecycle_with_fake_docker(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    project = client.post("/api/scripts", json=project_payload(), headers=admin_headers).json()
    assert client.post(f"/api/scripts/{project['id']}/file", json={"path": "/main.py", "content": "print(1)\n"}, headers=admin_headers).status_code == 200

    submitted = client.post(f"/api/scripts/{project['id']}/runs", headers=admin_headers)
    assert submitted.status_code == 200
    run_id = submitted.json()["run_id"]

    final = wait_run(client, admin_headers, run_id, {"success", "failed", "timeout"})
    assert final["status"] == "success"
    assert final["exit_code"] == 0

    run_log = client.get(f"/api/scripts/runs/{run_id}/log", headers=admin_headers)
    assert run_log.status_code == 200
    assert "script finished" in run_log.json()["logs"]

    runs = client.get(f"/api/scripts/{project['id']}/runs", headers=admin_headers)
    assert any(item["run_id"] == run_id and item["status"] == "success" for item in page_items(runs))

    environment = client.get(f"/api/scripts/{project['id']}/environment", headers=admin_headers)
    assert environment.status_code == 200
    assert environment.json()["available"] is True
    assert "Python" in environment.json()["language_version"]

    logs = client.get("/api/audit-logs", params={"actor_scope": "all", "action": "script.run"}, headers=admin_headers)
    assert any(item["action"] == "script.run" for item in page_items(logs))


def test_script_run_cancel(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    engine = install_fake_docker(monkeypatch)
    engine.hold_runs = True

    project = client.post("/api/scripts", json=project_payload(), headers=admin_headers).json()
    submitted = client.post(f"/api/scripts/{project['id']}/runs", headers=admin_headers)
    run_id = submitted.json()["run_id"]

    wait_run(client, admin_headers, run_id, {"running"})
    canceled = client.post(f"/api/scripts/runs/{run_id}/cancel", headers=admin_headers)
    assert canceled.status_code == 200
    assert canceled.json()["status"] == "canceled"

    time.sleep(0.3)
    final = client.get(f"/api/scripts/runs/{run_id}", headers=admin_headers)
    assert final.json()["status"] == "canceled"


def test_script_schedule_crud(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    project = client.post("/api/scripts", json=project_payload(), headers=admin_headers).json()
    pid = project["id"]

    interval = client.post(
        f"/api/scripts/{pid}/schedules",
        json={"name": "每分钟", "trigger_type": "interval", "interval_seconds": 60, "cron_expr": "", "enabled": True},
        headers=admin_headers,
    )
    assert interval.status_code == 200
    assert interval.json()["next_run_at"] is not None

    cron = client.post(
        f"/api/scripts/{pid}/schedules",
        json={"name": "每天两点", "trigger_type": "cron", "interval_seconds": None, "cron_expr": "0 2 * * *", "enabled": True},
        headers=admin_headers,
    )
    assert cron.status_code == 200

    invalid_cron = client.post(
        f"/api/scripts/{pid}/schedules",
        json={"name": "坏表达式", "trigger_type": "cron", "interval_seconds": None, "cron_expr": "not a cron", "enabled": True},
        headers=admin_headers,
    )
    assert invalid_cron.status_code == 400
    assert invalid_cron.json()["detail"]["code"] == "error.scriptCronInvalid"

    invalid_interval = client.post(
        f"/api/scripts/{pid}/schedules",
        json={"name": "缺间隔", "trigger_type": "interval", "interval_seconds": None, "cron_expr": "", "enabled": True},
        headers=admin_headers,
    )
    assert invalid_interval.status_code == 400
    assert invalid_interval.json()["detail"]["code"] == "error.scriptScheduleInvalid"

    listed = client.get(f"/api/scripts/{pid}/schedules", headers=admin_headers)
    assert len(listed.json()) == 2

    disabled = client.put(
        f"/api/scripts/schedules/{interval.json()['id']}",
        json={"name": "每分钟", "trigger_type": "interval", "interval_seconds": 120, "cron_expr": "", "enabled": False},
        headers=admin_headers,
    )
    assert disabled.status_code == 200
    assert disabled.json()["enabled"] is False
    assert disabled.json()["next_run_at"] is None

    deleted = client.delete(f"/api/scripts/schedules/{cron.json()['id']}", headers=admin_headers)
    assert deleted.status_code == 200
    assert len(client.get(f"/api/scripts/{pid}/schedules", headers=admin_headers).json()) == 1


def test_script_images_and_openapi_visibility(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    images = client.get("/api/scripts/images", headers=admin_headers)
    assert images.status_code == 200
    body = images.json()
    assert body["docker_available"] is True
    assert any(preset["image"] == "python:3.12-slim" and preset["available"] for preset in body["presets"])

    token = client.post("/api/tokens", json={"name": "脚本集成", "expires_at": None}, headers=admin_headers)
    assert token.status_code == 200
    api_headers = {"Authorization": f"Bearer {token.json()['token']}"}
    web_only = client.get("/api/scripts", headers=api_headers)
    assert web_only.status_code == 403
    assert web_only.json()["detail"]["code"] == "error.webOnly"

    openapi = client.get("/openapi.json", headers=admin_headers).json()
    assert not any(path.startswith("/api/scripts") for path in openapi["paths"])
    visible_tags = {
        tag
        for path_item in openapi["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict)
        for tag in operation.get("tags", [])
    }
    assert "scripts" not in visible_tags


def test_script_archive_upload_extracts(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    project = client.post("/api/scripts", json=project_payload(), headers=admin_headers).json()
    pid = project["id"]

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("main.py", "print('hi')\n")
        zf.writestr("pkg/util.py", "x = 1\n")
    archive.seek(0)

    upload = client.post(
        f"/api/scripts/{pid}/upload",
        params={"path": "/"},
        files={"file": ("code.zip", archive, "application/zip")},
        headers=admin_headers,
    )
    assert upload.status_code == 200

    names = {entry["name"] for entry in client.get(f"/api/scripts/{pid}/files", headers=admin_headers).json()["entries"]}
    assert {"main.py", "pkg"}.issubset(names)
    sub = client.get(f"/api/scripts/{pid}/files", params={"path": "/pkg"}, headers=admin_headers)
    assert [entry["name"] for entry in sub.json()["entries"]] == ["util.py"]

    logs = client.get("/api/audit-logs", params={"actor_scope": "all", "action": "script.archive_extract"}, headers=admin_headers)
    assert any(item["action"] == "script.archive_extract" for item in page_items(logs))


def test_script_archive_upload_rejects_unsafe_paths(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    project = client.post("/api/scripts", json=project_payload(), headers=admin_headers).json()
    pid = project["id"]

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.py", "print('escape')\n")
        zf.writestr("main.py", "print('ok')\n")
    archive.seek(0)

    upload = client.post(
        f"/api/scripts/{pid}/upload",
        params={"path": "/"},
        files={"file": ("code.zip", archive, "application/zip")},
        headers=admin_headers,
    )
    assert upload.status_code == 400
    assert upload.json()["detail"]["code"] == "error.scriptArchiveInvalid"

    entries = client.get(f"/api/scripts/{pid}/files", headers=admin_headers).json()["entries"]
    assert entries == []


def test_script_sharing_visibility_and_edit_scope(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])
    install_fake_docker(monkeypatch)

    role_id, _ = grant_script_role(client, admin_headers, "script_share_user", SCRIPT_BASE_CODES)
    owner = create_script_user(client, admin_headers, "script_owner", role_id, "13800000061")
    other = create_script_user(client, admin_headers, "script_other", role_id, "13800000062")

    shared = client.post("/api/scripts", json=project_payload(name="共享脚本", is_shared=True), headers=owner)
    assert shared.status_code == 200
    assert shared.json()["is_shared"] is True
    sid = shared.json()["id"]
    private = client.post("/api/scripts", json=project_payload(name="私有脚本"), headers=owner).json()

    visible_ids = {item["id"] for item in page_items(client.get("/api/scripts", headers=other))}
    assert sid in visible_ids
    assert private["id"] not in visible_ids

    # Shared project: another user can run it.
    assert client.post(f"/api/scripts/{sid}/runs", headers=other).status_code == 200

    # But cannot edit config or files (creator/admin only).
    denied_update = client.put(f"/api/scripts/{sid}", json=project_payload(name="改", is_shared=True), headers=other)
    assert denied_update.status_code == 403
    assert denied_update.json()["detail"]["code"] == "error.scriptManageOthersDenied"
    denied_write = client.post(f"/api/scripts/{sid}/file", json={"path": "/x.py", "content": "x"}, headers=other)
    assert denied_write.status_code == 403
