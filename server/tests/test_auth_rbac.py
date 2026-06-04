import importlib
import json
from pathlib import Path
import re

from fastapi.testclient import TestClient

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
            "company": "公司",
            "department": "部门",
            "full_name": "用户",
        },
    )
    assert register_response.status_code == 200
    assert client.post("/api/auth/login", json={"username": "user01", "password": "UserPass123"}).status_code == 400

    pending = client.get("/api/users", params={"approval_status": "pending"}, headers=admin_headers)
    assert pending.status_code == 200
    user_id = pending.json()[0]["id"]
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
        json={"full_name": "新管理员", "company": "新公司", "department": "新部门"},
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
