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


def sqlite_datetime(value: datetime) -> str:
    return value.isoformat(sep=" ")


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
    assert response.json() == {"code": "install.connectionOk", "message": "Database connection is healthy", "params": {}}
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
        AUDIT_LOG_MANAGE_OTHERS,
        AUDIT_LOG_READ,
        ANNOUNCEMENT_MANAGE_OTHERS,
        ANNOUNCEMENT_READ,
        API_DOCS_READ,
        API_TOKEN_CREATE,
        API_TOKEN_DELETE,
        API_TOKEN_READ,
        DEPRECATED_PERMISSION_CODES,
        PERMISSION_SEEDS,
        ROLE_READ,
        ROUTE_API_DOCS,
        ROUTE_AUDIT_LOGS,
        ROUTE_ANNOUNCEMENTS,
        ROUTE_PERMISSIONS,
        ROUTE_SETTINGS,
        ROUTE_TOKENS,
        ROUTE_READ_PERMISSIONS,
        ROUTE_USERS,
        SETTING_OPERATE,
        SETTING_READ,
        SETTING_UPDATE,
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
    assert seeds_by_code[ROUTE_USERS].name == "permission.route:users"
    assert seeds_by_code[ROUTE_USERS].group_name == "permission.group.page"
    assert seeds_by_code[ROUTE_USERS].description == "permission.description.route:users"
    assert seeds_by_code[USER_READ].type == "action"
    assert seeds_by_code[USER_READ].name == "permission.action:user:read"
    assert seeds_by_code[USER_READ].group_name == "permission.group.user"
    assert seeds_by_code[USER_READ].description == "permission.description.action:user:read"
    assert all(
        not re.search(r"[\u4e00-\u9fff]", f"{seed.name}{seed.group_name}{seed.description}")
        for seed in PERMISSION_SEEDS
    )
    assert ANNOUNCEMENT_MANAGE_OTHERS in seeds_by_code
    assert AUDIT_LOG_MANAGE_OTHERS in seeds_by_code
    assert seeds_by_code[AUDIT_LOG_READ].resource == "audit_log"
    assert seeds_by_code[SETTING_READ].resource == "setting"
    assert SETTING_UPDATE in seeds_by_code
    assert SETTING_OPERATE in seeds_by_code
    assert seeds_by_code[API_TOKEN_READ].resource == "api_token"
    assert API_TOKEN_CREATE in seeds_by_code
    assert API_TOKEN_DELETE in seeds_by_code
    assert seeds_by_code[API_DOCS_READ].resource == "api_docs"
    assert "action:announcement:operate" in DEPRECATED_PERMISSION_CODES
    assert "action:announcement:operate" not in seeds_by_code
    assert ROUTE_READ_PERMISSIONS == {
        ROUTE_USERS: USER_READ,
        ROUTE_PERMISSIONS: ROLE_READ,
        ROUTE_ANNOUNCEMENTS: ANNOUNCEMENT_READ,
        ROUTE_AUDIT_LOGS: AUDIT_LOG_READ,
        ROUTE_SETTINGS: SETTING_READ,
        ROUTE_TOKENS: API_TOKEN_READ,
        ROUTE_API_DOCS: API_DOCS_READ,
    }
    assert expand_permissions({ROUTE_USERS}) == {ROUTE_USERS, USER_READ}
    assert expand_permissions({ROUTE_TOKENS, ROUTE_API_DOCS}) == {ROUTE_TOKENS, API_TOKEN_READ, ROUTE_API_DOCS, API_DOCS_READ}


def test_api_docs_require_permission_and_use_local_assets(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    assert client.get("/docs").status_code == 401
    assert client.get("/openapi.json").status_code == 401

    response = client.get("/docs", headers=admin_headers)
    assert response.status_code == 200
    assert "http://" not in response.text
    assert "https://" not in response.text
    assert "/static/swagger-ui/swagger-ui-bundle.js" in response.text
    assert "/openapi.json" in response.text

    openapi = client.get("/openapi.json", headers=admin_headers)
    assert openapi.status_code == 200
    openapi_schema = openapi.json()
    assert openapi_schema["openapi"].startswith("3.")
    hidden_prefixes = (
        "/api/auth",
        "/api/health",
        "/api/install",
        "/api/permissions",
        "/api/roles",
        "/api/settings",
        "/api/tokens",
        "/api/users",
    )
    for prefix in hidden_prefixes:
        assert not any(path.startswith(prefix) for path in openapi_schema["paths"])
    hidden_tags = {"api-tokens", "auth", "health", "install", "roles", "settings", "users"}
    visible_tags = {
        tag
        for path_item in openapi_schema["paths"].values()
        for operation in path_item.values()
        for tag in operation.get("tags", [])
    }
    assert visible_tags.isdisjoint(hidden_tags)


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
    assert register_response.json()["code"] == "auth.registerSubmitted"
    assert client.post("/api/auth/login", json={"username": "user01", "password": "UserPass123"}).status_code == 400

    pending = client.get("/api/users", params={"approval_status": "pending"}, headers=admin_headers)
    assert pending.status_code == 200
    user_id = page_items(pending)[0]["id"]
    approve = client.post(f"/api/users/{user_id}/approve", json={"role_ids": []}, headers=admin_headers)
    assert approve.status_code == 200

    user_headers = login(client, "user01", "UserPass123")
    assert client.get("/api/users", headers=user_headers).status_code == 403
    assert client.get("/api/dashboard/summary", headers=user_headers).status_code == 200


def test_register_without_approval_can_login(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    settings_payload = client.get("/api/settings", headers=admin_headers).json()
    settings_payload["registration_approval_required"] = False
    assert client.put("/api/settings", json=settings_payload, headers=admin_headers).status_code == 200

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": "direct_user",
            "password": "UserPass123",
            "phone": "13800000004",
            "email": "direct_user@example.com",
            "company": "公司",
            "department": "部门",
            "full_name": "免审用户",
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["code"] == "auth.registerSuccess"

    users = client.get("/api/users", params={"keyword": "direct_user"}, headers=admin_headers)
    assert users.status_code == 200
    user = page_items(users)[0]
    assert user["approval_status"] == "approved"
    assert {role["code"] for role in user["roles"]} == {"user"}

    user_headers = login(client, "direct_user", "UserPass123")
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


def test_api_tokens_follow_role_permissions_and_api_feature_toggle(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    permissions = client.get("/api/permissions", headers=admin_headers).json()
    permission_ids_by_code = {item["code"]: item["id"] for item in permissions}
    for code in [
        "route:dashboard",
        "route:tokens",
        "route:api_docs",
        "route:announcements",
        "action:announcement:create",
        "action:api_token:create",
        "action:api_token:delete",
    ]:
        assert code in permission_ids_by_code

    role = client.post(
        "/api/roles",
        json={"code": "api_operator", "name": "API 操作员", "description": ""},
        headers=admin_headers,
    )
    assert role.status_code == 200
    role_id = role.json()["id"]
    assign = client.put(
        f"/api/roles/{role_id}/permissions",
        json={
            "permission_ids": [
                permission_ids_by_code[code]
                for code in [
                    "route:dashboard",
                    "route:tokens",
                    "route:api_docs",
                    "route:announcements",
                    "action:announcement:create",
                    "action:api_token:create",
                    "action:api_token:delete",
                ]
            ]
        },
        headers=admin_headers,
    )
    assert assign.status_code == 200

    user = client.post(
        "/api/users",
        json={
            "username": "api_user",
            "password": "ApiPass123",
            "full_name": "API 用户",
            "phone": "13800000009",
            "email": "api-user@example.com",
            "company": "",
            "department": "",
            "role_ids": [role_id],
        },
        headers=admin_headers,
    )
    assert user.status_code == 200
    user_headers = login(client, "api_user", "ApiPass123")

    me = client.get("/api/auth/me", headers=user_headers).json()
    assert "route:tokens" in me["permissions"]
    assert "action:api_token:read" in me["permissions"]
    assert "action:api_docs:read" in me["permissions"]

    created = client.post("/api/tokens", json={"name": "自动化调用", "expires_at": None}, headers=user_headers)
    assert created.status_code == 200
    created_data = created.json()
    assert created_data["token"].startswith("mtx_")
    assert created_data["token_prefix"] == created_data["token"][:12]
    assert created_data["secret_available"] is True
    assert created_data["expires_at"] is None
    assert "token_hash" not in created_data

    secret = client.get(f"/api/tokens/{created_data['id']}/secret", headers=user_headers)
    assert secret.status_code == 200
    assert secret.json()["token"] == created_data["token"]

    listed = client.get("/api/tokens", headers=user_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["secret_available"] is True
    assert "token" not in listed.json()[0]

    other = client.post(
        "/api/users",
        json={
            "username": "api_other",
            "password": "ApiPass123",
            "full_name": "API 其他用户",
            "phone": "13800000010",
            "email": "api-other@example.com",
            "company": "",
            "department": "",
            "role_ids": [role_id],
        },
        headers=admin_headers,
    )
    assert other.status_code == 200
    other_headers = login(client, "api_other", "ApiPass123")
    other_listed = client.get("/api/tokens", headers=other_headers)
    assert other_listed.status_code == 200
    assert other_listed.json() == []
    assert client.get(f"/api/tokens/{created_data['id']}/secret", headers=other_headers).status_code == 404

    reveal_disabled_settings = client.get("/api/settings", headers=admin_headers).json()
    reveal_disabled_settings["api_token_reveal_enabled"] = False
    assert client.put("/api/settings", json=reveal_disabled_settings, headers=admin_headers).status_code == 200
    reveal_disabled = client.get(f"/api/tokens/{created_data['id']}/secret", headers=user_headers)
    assert reveal_disabled.status_code == 403
    assert reveal_disabled.json()["detail"]["code"] == "error.apiTokenRevealDisabled"
    reveal_enabled_settings = client.get("/api/settings", headers=admin_headers).json()
    reveal_enabled_settings["api_token_reveal_enabled"] = True
    assert client.put("/api/settings", json=reveal_enabled_settings, headers=admin_headers).status_code == 200

    api_headers = {"Authorization": f"Bearer {created_data['token']}"}
    assert client.get("/api/dashboard/summary", headers=api_headers).status_code == 200
    web_only_paths = [
        "/api/auth/me",
        "/api/settings",
        "/api/users",
        "/api/roles",
        "/api/permissions",
        "/api/tokens",
    ]
    for path in web_only_paths:
        response = client.get(path, headers=api_headers)
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "error.webOnly"
    assert client.get("/openapi.json", headers=api_headers).status_code == 200

    api_announcement = client.post(
        "/api/announcements",
        json={
            "title": "API 创建公告",
            "content": "API Token 写操作来源验证",
            "target_type": "authenticated",
            "target_value": "",
            "show_popup": False,
            "show_ticker": True,
            "show_sidebar": True,
            "is_active": True,
        },
        headers=api_headers,
    )
    assert api_announcement.status_code == 200
    api_audit_logs = client.get(
        "/api/audit-logs",
        params={"actor_scope": "all", "action": "announcement.create"},
        headers=admin_headers,
    )
    assert api_audit_logs.status_code == 200
    api_log = next(item for item in page_items(api_audit_logs) if item["detail"] == "API 创建公告")
    assert api_log["source"] == "api"
    assert api_log["api_token_prefix"] == created_data["token_prefix"]
    assert api_log["detail_data"]["target_name"] == "API 创建公告"
    assert api_log["detail_data"]["meta"]["title"] == "API 创建公告"
    source_filtered_logs = client.get(
        "/api/audit-logs",
        params={"actor_scope": "all", "source": "api", "page_size": 500},
        headers=admin_headers,
    )
    assert source_filtered_logs.status_code == 200
    assert source_filtered_logs.json()["total"] >= 1
    assert all(item["source"] == "api" for item in page_items(source_filtered_logs))
    web_login_logs = client.get("/api/audit-logs", params={"actor_scope": "all", "action": "auth.login"}, headers=admin_headers)
    assert web_login_logs.status_code == 200
    assert all(item["source"] == "web" for item in page_items(web_login_logs))

    deleted = client.delete(f"/api/tokens/{created_data['id']}", headers=user_headers)
    assert deleted.status_code == 200
    assert deleted.json()["code"] == "token.deleted"
    assert client.get("/api/dashboard/summary", headers=api_headers).status_code == 401

    second_token = client.post("/api/tokens", json={"name": "关闭开关验证", "expires_at": None}, headers=user_headers).json()["token"]
    disabled_settings = client.get("/api/settings", headers=admin_headers).json()
    disabled_settings["api_enabled"] = False
    assert client.put("/api/settings", json=disabled_settings, headers=admin_headers).status_code == 200

    disabled_api_headers = {"Authorization": f"Bearer {second_token}"}
    disabled_token_call = client.get("/api/dashboard/summary", headers=disabled_api_headers)
    assert disabled_token_call.status_code == 403
    assert disabled_token_call.json()["detail"]["code"] == "error.apiDisabled"
    disabled_token_page = client.get("/api/tokens", headers=user_headers)
    assert disabled_token_page.status_code == 403
    assert disabled_token_page.json()["detail"]["code"] == "error.apiDisabled"
    disabled_openapi = client.get("/openapi.json", headers=admin_headers)
    assert disabled_openapi.status_code == 403
    assert disabled_openapi.json()["detail"]["code"] == "error.apiDisabled"


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
                {"created_at": sqlite_datetime(created_at), "username": username},
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
    assert forbidden_update.json()["detail"]["code"] == "error.announcementManageOthersDenied"
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
    assert allowed_batch_delete.json() == {"code": "announcement.batchDeleted", "message": "Announcements deleted", "params": {"count": 1}}


def test_audit_logs_scope_permission_controls_owner_filter(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    permissions = client.get("/api/permissions", headers=admin_headers).json()
    permission_ids_by_code = {item["code"]: item["id"] for item in permissions}
    assert "route:audit_logs" in permission_ids_by_code
    assert "action:audit_log:read" in permission_ids_by_code
    assert "action:audit_log:manage_others" in permission_ids_by_code

    role = client.post(
        "/api/roles",
        json={"code": "audit_reader", "name": "日志查看", "description": ""},
        headers=admin_headers,
    )
    assert role.status_code == 200
    role_id = role.json()["id"]
    assign = client.put(
        f"/api/roles/{role_id}/permissions",
        json={"permission_ids": [permission_ids_by_code["route:audit_logs"]]},
        headers=admin_headers,
    )
    assert assign.status_code == 200

    user = client.post(
        "/api/users",
        json={
            "username": "audit_reader",
            "password": "Audit123",
            "full_name": "日志查看",
            "phone": "13800000008",
            "email": "audit-reader@example.com",
            "company": "",
            "department": "",
            "role_ids": [role_id],
        },
        headers=admin_headers,
    )
    assert user.status_code == 200
    reader_headers = login(client, "audit_reader", "Audit123")

    me = client.get("/api/auth/me", headers=reader_headers).json()
    assert "route:audit_logs" in me["permissions"]
    assert "action:audit_log:read" in me["permissions"]

    self_logs = client.get("/api/audit-logs", headers=reader_headers)
    assert self_logs.status_code == 200
    assert self_logs.json()["total"] >= 1
    assert {item["actor_username"] for item in page_items(self_logs)} == {"audit_reader"}

    forbidden_all = client.get("/api/audit-logs", params={"actor_scope": "all"}, headers=reader_headers)
    assert forbidden_all.status_code == 403
    assert forbidden_all.json()["detail"]["code"] == "error.auditLogManageOthersDenied"

    forbidden_export_all = client.get("/api/audit-logs/export", params={"actor_scope": "all"}, headers=reader_headers)
    assert forbidden_export_all.status_code == 403
    assert forbidden_export_all.json()["detail"]["code"] == "error.auditLogManageOthersDenied"

    assign_all = client.put(
        f"/api/roles/{role_id}/permissions",
        json={
            "permission_ids": [
                permission_ids_by_code["route:audit_logs"],
                permission_ids_by_code["action:audit_log:manage_others"],
            ]
        },
        headers=admin_headers,
    )
    assert assign_all.status_code == 200

    all_logs = client.get(
        "/api/audit-logs",
        params={"actor_scope": "all", "keyword": payload["admin_username"], "page_size": 500},
        headers=reader_headers,
    )
    assert all_logs.status_code == 200
    assert payload["admin_username"] in {item["actor_username"] for item in page_items(all_logs)}

    exported = client.get(
        "/api/audit-logs/export",
        params={"actor_scope": "all", "keyword": payload["admin_username"], "sort_order": "ascend"},
        headers=reader_headers,
    )
    assert exported.status_code == 200
    assert exported.headers["content-type"].startswith("text/csv")
    assert exported.headers["content-disposition"] == 'attachment; filename="audit-logs.csv"'
    assert exported.text.startswith("\ufeffid,operator,source,action,target_type,target_id,detail,created_at")
    assert payload["admin_username"] in exported.text

    login_logs = client.get("/api/audit-logs", params={"action": "auth.login"}, headers=reader_headers)
    assert login_logs.status_code == 200
    assert all(item["action"] == "auth.login" for item in page_items(login_logs))


def test_system_settings_control_registration_retention_and_backup(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    admin_headers = login(client, payload["admin_username"], payload["admin_password"])

    public_defaults = client.get("/api/settings/public")
    assert public_defaults.status_code == 200
    assert public_defaults.json()["app_name"] == "Metrix"
    assert public_defaults.json()["registration_approval_required"] is True
    assert public_defaults.json()["api_enabled"] is True
    assert public_defaults.json()["api_token_reveal_enabled"] is True

    settings_payload = {
        "app_name": "Data Portal",
        "registration_enabled": False,
        "registration_approval_required": True,
        "registration_required_fields": {
            "phone": False,
            "email": False,
            "company": True,
            "department": True,
        },
        "log_retention_days": 7,
        "default_locale": "en-US",
        "api_enabled": True,
        "api_token_reveal_enabled": False,
    }
    updated = client.put("/api/settings", json=settings_payload, headers=admin_headers)
    assert updated.status_code == 200
    assert updated.json()["app_name"] == "Data Portal"
    assert updated.json()["api_token_reveal_enabled"] is False

    public_updated = client.get("/api/settings/public").json()
    assert public_updated["registration_enabled"] is False
    assert public_updated["registration_approval_required"] is True
    assert public_updated["default_locale"] == "en-US"
    assert public_updated["api_token_reveal_enabled"] is False
    disabled_register = client.post(
        "/api/auth/register",
        json={
            "username": "closed_register",
            "password": "UserPass123",
            "phone": "",
            "email": "",
            "company": "公司",
            "department": "岗位",
            "full_name": "关闭注册",
        },
    )
    assert disabled_register.status_code == 400
    assert disabled_register.json()["detail"]["code"] == "error.registrationDisabled"

    settings_payload["registration_enabled"] = True
    assert client.put("/api/settings", json=settings_payload, headers=admin_headers).status_code == 200
    missing_required = client.post(
        "/api/auth/register",
        json={
            "username": "missing_company",
            "password": "UserPass123",
            "phone": "",
            "email": "",
            "company": "",
            "department": "",
            "full_name": "缺少公司",
        },
    )
    assert missing_required.status_code == 400
    assert missing_required.json()["detail"]["code"] == "error.registrationFieldRequired"

    optional_contact = client.post(
        "/api/auth/register",
        json={
            "username": "optional_contact",
            "password": "UserPass123",
            "phone": "",
            "email": "",
            "company": "公司",
            "department": "岗位",
            "full_name": "可选联系方式",
        },
    )
    assert optional_contact.status_code == 200

    from app.core.install import load_install_config
    from app.services.maintenance import prune_audit_logs_once

    engine = create_engine(load_install_config().database_url)
    old_time = datetime(2026, 1, 1)
    latest_time = datetime(2026, 1, 20)
    with engine.begin() as conn:
        actor_id = conn.execute(text("SELECT id FROM users WHERE username = 'optional_contact'")).scalar_one()
        conn.execute(
            text(
                "INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, detail, created_at) "
                "VALUES (:actor_id, 'test.old', 'system', '', 'old', :created_at)"
            ),
            {"actor_id": actor_id, "created_at": sqlite_datetime(old_time)},
        )
        conn.execute(
            text(
                "INSERT INTO audit_logs (actor_user_id, action, target_type, target_id, detail, created_at) "
                "VALUES (:actor_id, 'test.latest', 'system', '', 'latest', :created_at)"
            ),
            {"actor_id": actor_id, "created_at": sqlite_datetime(latest_time)},
        )
    engine.dispose()

    prune_audit_logs_once()
    exported_logs = client.get("/api/audit-logs/export", params={"actor_scope": "all", "keyword": "test."}, headers=admin_headers)
    assert "test.latest" in exported_logs.text
    assert "test.old" not in exported_logs.text

    settings_payload["app_name"] = "Data Portal 2"
    assert client.put("/api/settings", json=settings_payload, headers=admin_headers).status_code == 200
    backup = client.post("/api/settings/backup", headers=admin_headers)
    assert backup.status_code == 200
    assert backup.headers["content-type"] == "application/zip"
    settings_logs = client.get("/api/audit-logs", params={"actor_scope": "all", "target_type": "system_settings"}, headers=admin_headers)
    assert settings_logs.status_code == 200
    assert {"settings.update", "settings.backup"}.issubset({item["action"] for item in page_items(settings_logs)})
    update_log = next(item for item in page_items(settings_logs) if item["action"] == "settings.update")
    changed_fields = {item["field"] for item in update_log["detail_data"]["changes"]}
    assert {"app_name", "api_token_reveal_enabled"}.intersection(changed_fields)
    import zipfile
    from io import BytesIO

    with zipfile.ZipFile(BytesIO(backup.content)) as archive:
        names = set(archive.namelist())
        assert "metadata.json" in names
        assert "tables/users.json" in names
        assert "tables/system_settings.json" in names
        settings_rows = json.loads(archive.read("tables/system_settings.json").decode("utf-8"))
        assert any(row["key"] == "app_name" and row["value"] == "Data Portal 2" for row in settings_rows)


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
    assert batch_delete.json() == {"code": "announcement.batchDeleted", "message": "Announcements deleted", "params": {"count": 2}}
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
