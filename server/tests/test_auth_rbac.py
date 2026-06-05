import importlib
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.schemas.install import InstallDatabaseTestRequest, InstallRequest, MysqlInstallConfig

PROJECT_DIR = Path(__file__).resolve().parents[2]
MYSQL_TEST_DATABASE = "app_test"


def create_client(tmp_path, monkeypatch):
    monkeypatch.setenv("METRIX_RUNTIME_DIR", str(tmp_path / "runtime"))
    from app.core.config import get_settings
    from app.db.session import reset_engine

    get_settings.cache_clear()
    reset_engine()
    main = importlib.import_module("app.main")
    return TestClient(main.create_app())


def install_sqlite(client: TestClient, tmp_path):
    db_path = tmp_path / "site.db"
    payload = {
        "database_type": "sqlite",
        "sqlite_path": str(db_path),
        "admin_username": "rootadmin",
        "admin_password": "RootPass123",
        "admin_full_name": "管理员",
        "admin_phone": "13800000000",
        "admin_email": "rootadmin@example.com",
        "admin_company": "平台公司",
        "admin_department": "平台",
    }
    response = client.post("/api/install", json=payload)
    assert response.status_code == 200
    assert db_path.exists()
    return payload


def login(client: TestClient, username: str, password: str) -> dict[str, str]:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def page_items(response):
    return response.json()["items"]


def create_announcement(client: TestClient, headers: dict[str, str], title: str):
    response = client.post(
        "/api/announcements",
        json={
            "title": title,
            "content": f"{title} 内容",
            "target_type": "authenticated",
            "target_value": "",
            "show_popup": False,
            "show_ticker": True,
            "show_sidebar": True,
            "is_active": True,
        },
        headers=headers,
    )
    assert response.status_code == 200
    return response


def slugify(value: str) -> str:
    return re.sub(r"(^_+|_+$)", "", re.sub(r"[^a-z0-9_]+", "_", value.strip().lower())) or "app"


def test_install_status_and_sqlite_install(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    assert client.get("/api/install/status").json() == {"installed": False, "database_type": None}

    payload = install_sqlite(client, tmp_path)

    status = client.get("/api/install/status").json()
    assert status == {"installed": True, "database_type": "sqlite"}
    assert client.post("/api/install", json=payload).status_code == 400


def test_sqlite_database_test_endpoint(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    db_path = tmp_path / "test-connection.db"

    response = client.post("/api/install/test-database", json={"database_type": "sqlite", "sqlite_path": str(db_path)})

    assert response.status_code == 200
    assert response.json() == {"message": "数据库连接正常"}
    assert db_path.exists()


def test_installed_database_auto_syncs_new_tables_and_permissions(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)

    from app.core.install import load_install_config
    from app.db.session import reset_engine

    engine = create_engine(load_install_config().database_url)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE announcement_reads"))
        conn.execute(text("DROP TABLE announcements"))
        conn.execute(text("DELETE FROM role_permissions WHERE permission_id IN (SELECT id FROM permissions WHERE resource = 'announcement')"))
        conn.execute(text("DELETE FROM permissions WHERE resource = 'announcement' OR code = 'route:announcements'"))
    engine.dispose()
    reset_engine()

    headers = login(client, payload["admin_username"], payload["admin_password"])

    announcements = client.get("/api/announcements", headers=headers)
    assert announcements.status_code == 200
    assert announcements.json()["items"] == []
    assert announcements.json()["total"] == 0

    permissions = client.get("/api/permissions", headers=headers)
    assert "route:announcements" in {item["code"] for item in permissions.json()}


def test_app_config_defaults_and_env_override(monkeypatch):
    from app.core.config import get_settings

    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("APP_SLUG", raising=False)
    monkeypatch.delenv("METRIX_APP_NAME", raising=False)
    monkeypatch.delenv("METRIX_APP_SLUG", raising=False)
    get_settings.cache_clear()
    app_config = json.loads((PROJECT_DIR / "app.config.json").read_text(encoding="utf-8"))
    settings = get_settings()
    assert settings.app_name == app_config["appName"]
    assert settings.app_slug == slugify(app_config["appName"])

    monkeypatch.setenv("APP_NAME", "Custom Portal")
    monkeypatch.setenv("APP_SLUG", "custom_portal")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.app_name == "Custom Portal"
    assert settings.app_slug == "custom_portal"
    get_settings.cache_clear()


def test_permission_specs_generate_codes_and_route_read_mapping():
    from app.core.permissions import (
        ANNOUNCEMENT_MANAGE_OTHERS,
        ANNOUNCEMENT_READ,
        DEPRECATED_PERMISSION_CODES,
        PERMISSION_SEEDS,
        ROLE_READ,
        ROUTE_ANNOUNCEMENTS,
        ROUTE_PERMISSIONS,
        ROUTE_READ_PERMISSIONS,
        ROUTE_USERS,
        USER_READ,
        action_code,
        expand_permissions,
        route_code,
    )

    seeds_by_code = {seed.code: seed for seed in PERMISSION_SEEDS}

    assert len(seeds_by_code) == len(PERMISSION_SEEDS)
    assert route_code("tasks") == "route:tasks"
    assert action_code("task", "start") == "action:task:start"
    assert seeds_by_code[ROUTE_USERS].type == "route"
    assert seeds_by_code[USER_READ].type == "action"
    assert ANNOUNCEMENT_MANAGE_OTHERS in seeds_by_code
    assert "action:announcement:operate" in DEPRECATED_PERMISSION_CODES
    assert "action:announcement:operate" not in seeds_by_code
    assert ROUTE_READ_PERMISSIONS == {
        ROUTE_USERS: USER_READ,
        ROUTE_PERMISSIONS: ROLE_READ,
        ROUTE_ANNOUNCEMENTS: ANNOUNCEMENT_READ,
    }
    assert expand_permissions({ROUTE_USERS}) == {ROUTE_USERS, USER_READ}


def test_api_docs_use_local_assets(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    response = client.get("/docs")
    assert response.status_code == 200
    assert "http://" not in response.text
    assert "https://" not in response.text
    assert "/static/swagger-ui/swagger-ui-bundle.js" in response.text


def test_mysql_install_runs_database_and_table_creation(monkeypatch):
    from app.services import install as install_service

    calls = []

    class FakeEngine:
        def __init__(self, url):
            self.url = url

        def dispose(self):
            calls.append(("dispose", self.url))

    class FakeSession:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeSessionFactory:
        def __call__(self):
            return FakeSession()

    payload = InstallRequest(
        database_type="mysql",
        mysql=MysqlInstallConfig(host="127.0.0.1", port=3306, database=MYSQL_TEST_DATABASE, username="root", password="pass"),
        admin_username="mysqladmin",
        admin_password="MysqlPass123",
        admin_full_name="MySQL 管理员",
        admin_phone="13800000001",
        admin_email="mysqladmin@example.com",
        admin_company="",
        admin_department="",
    )
    monkeypatch.setattr(install_service, "is_installed", lambda: False)
    monkeypatch.setattr(install_service, "_create_mysql_database", lambda data: calls.append(("create_db", data.mysql.database)))
    monkeypatch.setattr(install_service, "create_engine_for_url", lambda url: FakeEngine(url))
    monkeypatch.setattr(install_service, "create_tables", lambda engine: calls.append(("tables", engine.url)))
    monkeypatch.setattr(install_service, "sessionmaker", lambda **kwargs: FakeSessionFactory())
    monkeypatch.setattr(install_service, "seed_database", lambda db, data: calls.append(("seed", data.admin_username)))
    monkeypatch.setattr(install_service, "write_install_config", lambda database_type, url: calls.append(("config", database_type, url)))
    monkeypatch.setattr(install_service, "reset_engine", lambda: calls.append("reset"))

    install_service.install_system(payload)

    assert ("create_db", MYSQL_TEST_DATABASE) in calls
    assert any(call[0] == "tables" and call[1].startswith(f"mysql+pymysql://root:pass@127.0.0.1:3306/{MYSQL_TEST_DATABASE}") for call in calls)
    assert ("seed", "mysqladmin") in calls
    assert any(call[0] == "config" and call[1] == "mysql" for call in calls)
    assert "reset" in calls


def test_mysql_database_creation_sql(monkeypatch):
    from app.services import install as install_service

    statements = []

    class FakeConnection:
        def execute(self, statement):
            statements.append(str(statement))

    class FakeBegin:
        def __enter__(self):
            return FakeConnection()

        def __exit__(self, *args):
            return False

    class FakeEngine:
        def begin(self):
            return FakeBegin()

        def dispose(self):
            statements.append("disposed")

    payload = InstallRequest(
        database_type="mysql",
        mysql=MysqlInstallConfig(host="127.0.0.1", port=3306, database=MYSQL_TEST_DATABASE, username="root", password="pass"),
        admin_username="mysqladmin",
        admin_password="MysqlPass123",
        admin_full_name="MySQL 管理员",
        admin_phone="13800000001",
        admin_email="mysqladmin@example.com",
        admin_company="",
        admin_department="",
    )
    monkeypatch.setattr(install_service, "create_engine_for_url", lambda url: FakeEngine())

    install_service._create_mysql_database(payload)

    assert f"CREATE DATABASE IF NOT EXISTS `{MYSQL_TEST_DATABASE}`" in statements[0]
    assert "CHARACTER SET utf8mb4" in statements[0]
    assert "disposed" in statements


def test_mysql_database_test_uses_server_connection(monkeypatch):
    from app.services import install as install_service

    calls = []

    class FakeConnection:
        def __enter__(self):
            calls.append("connect")
            return self

        def __exit__(self, *args):
            return False

        def execute(self, statement):
            calls.append(str(statement))

    class FakeEngine:
        def __init__(self, url):
            self.url = url

        def connect(self):
            calls.append(("url", self.url))
            return FakeConnection()

        def dispose(self):
            calls.append("disposed")

    payload = InstallDatabaseTestRequest(
        database_type="mysql",
        mysql=MysqlInstallConfig(host="127.0.0.1", port=3306, database=MYSQL_TEST_DATABASE, username="root", password="pass"),
    )
    monkeypatch.setattr(install_service, "create_engine_for_url", lambda url: FakeEngine(url))

    install_service.test_database_connection(payload)

    assert ("url", "mysql+pymysql://root:pass@127.0.0.1:3306/?charset=utf8mb4") in calls
    assert "SELECT 1" in calls
    assert "disposed" in calls


def test_admin_login_and_dashboard(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    headers = login(client, payload["admin_username"], payload["admin_password"])

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert "route:dashboard" in me.json()["permissions"]

    summary = client.get("/api/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["user_count"] == 1


def test_register_approve_and_user_login(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "user01",
            "password": "UserPass123",
            "phone": "13800000002",
            "email": "user01@example.com",
            "company": "公司",
            "department": "部门",
            "full_name": "用户",
        },
    )
    assert register_response.status_code == 200
    assert client.post("/api/auth/login", json={"username": "user01", "password": "UserPass123"}).status_code == 400

    pending = client.get("/api/users", params={"approval_status": "pending"}, headers=admin_headers)
    assert pending.status_code == 200
    user_id = page_items(pending)[0]["id"]
    approve = client.post(f"/api/users/{user_id}/approve", json={"role_ids": []}, headers=admin_headers)
    assert approve.status_code == 200

    user_headers = login(client, "user01", "UserPass123")
    assert client.get("/api/users", headers=user_headers).status_code == 403
    assert client.get("/api/dashboard/summary", headers=user_headers).status_code == 200


def test_profile_and_password_change(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    headers = login(client, payload["admin_username"], payload["admin_password"])

    profile = client.put(
        "/api/auth/profile",
        json={
            "full_name": "新管理员",
            "phone": "13800000003",
            "email": "newadmin@example.com",
            "company": "新公司",
            "department": "新部门",
        },
        headers=headers,
    )
    assert profile.status_code == 200
    assert profile.json()["full_name"] == "新管理员"

    bad_change = client.post(
        "/api/auth/change-password",
        json={"old_password": "wrong", "new_password": "NewPass123"},
        headers=headers,
    )
    assert bad_change.status_code == 400

    good_change = client.post(
        "/api/auth/change-password",
        json={"old_password": payload["admin_password"], "new_password": "NewPass123"},
        headers=headers,
    )
    assert good_change.status_code == 200
    assert client.post("/api/auth/login", json={"username": payload["admin_username"], "password": "NewPass123"}).status_code == 200


def test_role_permission_controls_route_and_read_permission(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    role = client.post(
        "/api/roles",
        json={"code": "limited", "name": "受限角色", "description": ""},
        headers=admin_headers,
    )
    assert role.status_code == 200
    role_id = role.json()["id"]

    permissions = client.get("/api/permissions", headers=admin_headers).json()
    assert "route:approvals" not in {item["code"] for item in permissions}
    users_route = next(item for item in permissions if item["code"] == "route:users")
    user_operate = next(item for item in permissions if item["code"] == "action:user:operate")
    assign = client.put(f"/api/roles/{role_id}/permissions", json={"permission_ids": [users_route["id"], user_operate["id"]]}, headers=admin_headers)
    assert assign.status_code == 200

    user = client.post(
        "/api/users",
        json={
            "username": "reader",
            "password": "Reader123",
            "full_name": "查询员",
            "phone": "13800000004",
            "email": "reader@example.com",
            "company": "",
            "department": "",
            "role_ids": [role_id],
        },
        headers=admin_headers,
    )
    assert user.status_code == 200

    reader_headers = login(client, "reader", "Reader123")
    me = client.get("/api/auth/me", headers=reader_headers).json()
    assert "route:users" in me["permissions"]
    assert "action:user:read" in me["permissions"]
    assert client.get("/api/users", headers=reader_headers).status_code == 200
    role_options = client.get("/api/users/role-options", headers=reader_headers)
    assert role_options.status_code == 200
    assert role_options.json()[0].keys() == {"id", "code", "name"}
    assert client.get("/api/permissions", headers=reader_headers).status_code == 403
    assert client.post("/api/users", json={}, headers=reader_headers).status_code == 403


def test_user_list_supports_pagination(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    for index in range(3):
        response = client.post(
            "/api/users",
            json={
                "username": f"page_user_{index}",
                "password": "UserPass123",
                "full_name": f"分页用户{index}",
                "phone": f"1380000100{index}",
                "email": f"page_user_{index}@example.com",
                "company": "",
                "department": "",
                "role_ids": [],
            },
            headers=admin_headers,
        )
        assert response.status_code == 200

    from app.core.install import load_install_config

    created_times = {
        payload["admin_username"]: datetime(2026, 1, 1),
        "page_user_0": datetime(2026, 1, 2),
        "page_user_1": datetime(2026, 1, 3),
        "page_user_2": datetime(2026, 1, 4),
    }
    engine = create_engine(load_install_config().database_url)
    with engine.begin() as conn:
        for username, created_at in created_times.items():
            conn.execute(
                text("UPDATE users SET created_at = :created_at WHERE username = :username"),
                {"created_at": created_at, "username": username},
            )
    engine.dispose()

    first_page = client.get("/api/users", params={"page": 1, "page_size": 2}, headers=admin_headers)
    assert first_page.status_code == 200
    assert len(page_items(first_page)) == 2
    assert first_page.json()["total"] == 4
    assert first_page.json()["page"] == 1
    assert first_page.json()["page_size"] == 2

    second_page = client.get("/api/users", params={"page": 2, "page_size": 2}, headers=admin_headers)
    assert second_page.status_code == 200
    assert len(page_items(second_page)) == 2

    large_page = client.get("/api/users", params={"page_size": 500}, headers=admin_headers)
    assert large_page.status_code == 200
    assert large_page.json()["page_size"] == 500
    assert large_page.json()["total"] == 4

    ascending = client.get("/api/users", params={"page_size": 500, "sort_order": "ascend"}, headers=admin_headers)
    assert ascending.status_code == 200
    assert [item["username"] for item in page_items(ascending)] == [
        payload["admin_username"],
        "page_user_0",
        "page_user_1",
        "page_user_2",
    ]

    descending = client.get("/api/users", params={"page_size": 500, "sort_order": "descend"}, headers=admin_headers)
    assert descending.status_code == 200
    assert [item["username"] for item in page_items(descending)] == [
        "page_user_2",
        "page_user_1",
        "page_user_0",
        payload["admin_username"],
    ]

    by_time_range = client.get(
        "/api/users",
        params={
            "page_size": 500,
            "sort_order": "ascend",
            "start_time": (created_times["page_user_1"] - timedelta(seconds=1)).isoformat(),
            "end_time": (created_times["page_user_2"] + timedelta(seconds=1)).isoformat(),
        },
        headers=admin_headers,
    )
    assert by_time_range.status_code == 200
    assert [item["username"] for item in page_items(by_time_range)] == ["page_user_1", "page_user_2"]


def test_announcement_list_supports_pagination_sort_and_creator_filter(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    create_announcement(client, admin_headers, "公告一")
    create_announcement(client, admin_headers, "公告二")
    create_announcement(client, admin_headers, "公告三")

    permissions = client.get("/api/permissions", headers=admin_headers).json()
    announcement_permissions = [
        item["id"]
        for item in permissions
        if item["code"] in {"action:announcement:create", "action:announcement:read"}
    ]
    role = client.post(
        "/api/roles",
        json={"code": "notice_editor", "name": "公告编辑", "description": ""},
        headers=admin_headers,
    )
    assert role.status_code == 200
    assign = client.put(
        f"/api/roles/{role.json()['id']}/permissions",
        json={"permission_ids": announcement_permissions},
        headers=admin_headers,
    )
    assert assign.status_code == 200
    editor = client.post(
        "/api/users",
        json={
            "username": "notice_editor",
            "password": "Notice123",
            "full_name": "公告编辑",
            "phone": "13800000005",
            "email": "notice-editor@example.com",
            "company": "",
            "department": "",
            "role_ids": [role.json()["id"]],
        },
        headers=admin_headers,
    )
    assert editor.status_code == 200
    editor_headers = login(client, "notice_editor", "Notice123")
    create_announcement(client, editor_headers, "编辑公告")

    ascending = client.get(
        "/api/announcements",
        params={"page": 1, "page_size": 2, "sort_order": "ascend"},
        headers=admin_headers,
    )
    assert ascending.status_code == 200
    assert [item["title"] for item in page_items(ascending)] == ["公告一", "公告二"]
    assert ascending.json()["total"] == 4

    descending = client.get(
        "/api/announcements",
        params={"page": 1, "page_size": 2, "sort_order": "descend"},
        headers=admin_headers,
    )
    assert descending.status_code == 200
    assert [item["title"] for item in page_items(descending)] == ["编辑公告", "公告三"]

    admin_only = client.get("/api/announcements", params={"created_by": "me"}, headers=admin_headers)
    assert admin_only.status_code == 200
    assert {item["title"] for item in page_items(admin_only)} == {"公告一", "公告二", "公告三"}

    editor_only = client.get("/api/announcements", params={"created_by": "me"}, headers=editor_headers)
    assert editor_only.status_code == 200
    assert [item["title"] for item in page_items(editor_only)] == ["编辑公告"]

    all_creators = client.get("/api/announcements", params={"created_by": "all", "page_size": 500}, headers=admin_headers)
    assert all_creators.status_code == 200
    assert all_creators.json()["total"] == 4
    assert all_creators.json()["page_size"] == 500


def test_announcement_manage_others_permission_controls_cross_owner_actions(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    permissions = client.get("/api/permissions", headers=admin_headers).json()
    permission_ids_by_code = {item["code"]: item["id"] for item in permissions}
    base_codes = {
        "action:announcement:create",
        "action:announcement:read",
        "action:announcement:update",
        "action:announcement:delete",
    }
    assert "action:announcement:manage_others" in permission_ids_by_code
    assert "action:announcement:operate" not in permission_ids_by_code

    role = client.post(
        "/api/roles",
        json={"code": "notice_operator", "name": "公告操作员", "description": ""},
        headers=admin_headers,
    )
    assert role.status_code == 200
    role_id = role.json()["id"]
    assign = client.put(
        f"/api/roles/{role_id}/permissions",
        json={"permission_ids": [permission_ids_by_code[code] for code in base_codes]},
        headers=admin_headers,
    )
    assert assign.status_code == 200

    for username in ["notice_owner", "notice_other"]:
        user = client.post(
            "/api/users",
            json={
                "username": username,
                "password": "Notice123",
                "full_name": username,
                "phone": "13800000007",
                "email": f"{username}@example.com",
                "company": "",
                "department": "",
                "role_ids": [role_id],
            },
            headers=admin_headers,
        )
        assert user.status_code == 200

    owner_headers = login(client, "notice_owner", "Notice123")
    other_headers = login(client, "notice_other", "Notice123")
    owner_announcement = create_announcement(client, owner_headers, "本人公告").json()
    other_announcement = create_announcement(client, other_headers, "他人自己的公告").json()

    update_payload = {
        "title": "跨人修改",
        "content": "尝试修改他人公告",
        "target_type": "authenticated",
        "target_value": "",
        "show_popup": False,
        "show_ticker": True,
        "show_sidebar": True,
        "is_active": True,
    }
    forbidden_update = client.put(f"/api/announcements/{owner_announcement['id']}", json=update_payload, headers=other_headers)
    assert forbidden_update.status_code == 403
    assert forbidden_update.json()["detail"] == "无权限操作他人公告"
    assert client.delete(f"/api/announcements/{owner_announcement['id']}", headers=other_headers).status_code == 403
    assert client.post("/api/announcements/batch-delete", json={"ids": [owner_announcement["id"]]}, headers=other_headers).status_code == 403

    own_update = client.put(f"/api/announcements/{other_announcement['id']}", json=update_payload, headers=other_headers)
    assert own_update.status_code == 200
    assert own_update.json()["title"] == "跨人修改"

    assign_with_manage_others = client.put(
        f"/api/roles/{role_id}/permissions",
        json={
            "permission_ids": [
                permission_ids_by_code[code]
                for code in {*base_codes, "action:announcement:manage_others"}
            ]
        },
        headers=admin_headers,
    )
    assert assign_with_manage_others.status_code == 200

    allowed_update = client.put(f"/api/announcements/{owner_announcement['id']}", json=update_payload, headers=other_headers)
    assert allowed_update.status_code == 200
    assert allowed_update.json()["title"] == "跨人修改"
    assert client.delete(f"/api/announcements/{owner_announcement['id']}", headers=other_headers).status_code == 200

    batch_target = create_announcement(client, owner_headers, "跨人批量删除").json()
    allowed_batch_delete = client.post("/api/announcements/batch-delete", json={"ids": [batch_target["id"]]}, headers=other_headers)
    assert allowed_batch_delete.status_code == 200
    assert allowed_batch_delete.json() == {"message": "已删除 1 条公告"}


def test_announcements_public_targeted_and_read_state(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    public = client.post(
        "/api/announcements",
        json={
            "title": "平台维护",
            "content": "今晚进行平台维护",
            "target_type": "all",
            "target_value": "",
            "show_popup": False,
            "show_ticker": True,
            "show_sidebar": True,
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert public.status_code == 200
    assert public.json()["created_by_username"] == payload["admin_username"]

    targeted = client.post(
        "/api/announcements",
        json={
            "title": "部门通知",
            "content": "请关注部门任务安排",
            "target_type": "company_department",
            "target_value": "公司|部门",
            "show_popup": True,
            "show_ticker": True,
            "show_sidebar": True,
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert targeted.status_code == 200

    authenticated = client.post(
        "/api/announcements",
        json={
            "title": "登录用户公告",
            "content": "只对已登录用户显示",
            "target_type": "authenticated",
            "target_value": "",
            "show_popup": False,
            "show_ticker": True,
            "show_sidebar": True,
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert authenticated.status_code == 200

    listed = client.get("/api/announcements", headers=admin_headers)
    assert listed.status_code == 200
    assert all(item["created_by_username"] == payload["admin_username"] for item in page_items(listed))

    all_target = client.get("/api/announcements", params={"target_type": "all"}, headers=admin_headers)
    assert [item["title"] for item in page_items(all_target)] == ["平台维护"]

    popup_items = client.get("/api/announcements", params={"display_mode": "popup"}, headers=admin_headers)
    assert [item["title"] for item in page_items(popup_items)] == ["部门通知"]

    keyword_items = client.get("/api/announcements", params={"keyword": "登录用户"}, headers=admin_headers)
    assert [item["title"] for item in page_items(keyword_items)] == ["登录用户公告"]

    batch_delete_ids = []
    for title in ["待批量删除一", "待批量删除二"]:
        item = client.post(
            "/api/announcements",
            json={
                "title": title,
                "content": "批量删除验证",
                "target_type": "authenticated",
                "target_value": "",
                "show_popup": False,
                "show_ticker": False,
                "show_sidebar": True,
                "is_active": True,
            },
            headers=admin_headers,
        )
        assert item.status_code == 200
        batch_delete_ids.append(item.json()["id"])
    batch_delete = client.post("/api/announcements/batch-delete", json={"ids": batch_delete_ids}, headers=admin_headers)
    assert batch_delete.status_code == 200
    assert batch_delete.json() == {"message": "已删除 2 条公告"}
    remaining_titles = {item["title"] for item in page_items(client.get("/api/announcements", headers=admin_headers))}
    assert "待批量删除一" not in remaining_titles
    assert "待批量删除二" not in remaining_titles

    public_items = client.get("/api/announcements/public").json()
    assert [item["title"] for item in public_items] == ["平台维护"]

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "notice_user",
            "password": "Notice123",
            "phone": "13800000006",
            "email": "notice-user@example.com",
            "company": "公司",
            "department": "部门",
            "full_name": "公告用户",
        },
    )
    assert register_response.status_code == 200
    pending = client.get("/api/users", params={"approval_status": "pending"}, headers=admin_headers)
    user_id = next(item["id"] for item in page_items(pending) if item["username"] == "notice_user")
    assert client.post(f"/api/users/{user_id}/approve", json={"role_ids": []}, headers=admin_headers).status_code == 200

    user_headers = login(client, "notice_user", "Notice123")
    feed = client.get("/api/announcements/mine", headers=user_headers)
    assert feed.status_code == 200
    feed_by_title = {item["title"]: item for item in feed.json()}
    assert set(feed_by_title) == {"平台维护", "部门通知", "登录用户公告"}
    assert feed_by_title["部门通知"]["is_read"] is False

    read = client.post(f"/api/announcements/{targeted.json()['id']}/read", headers=user_headers)
    assert read.status_code == 200
    assert read.json()["is_read"] is True

    updated_feed = client.get("/api/announcements/mine", headers=user_headers).json()
    assert next(item for item in updated_feed if item["title"] == "部门通知")["is_read"] is True
