import importlib

from fastapi.testclient import TestClient


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
        "admin_company": "Metrix",
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


def test_install_status_and_sqlite_install(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    assert client.get("/api/install/status").json() == {"installed": False, "database_type": None}

    payload = install_sqlite(client, tmp_path)

    status = client.get("/api/install/status").json()
    assert status == {"installed": True, "database_type": "sqlite"}
    assert client.post("/api/install", json=payload).status_code == 400


def test_api_docs_use_local_assets(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    response = client.get("/docs")
    assert response.status_code == 200
    assert "http://" not in response.text
    assert "https://" not in response.text
    assert "/static/swagger-ui/swagger-ui-bundle.js" in response.text


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

    pending = client.get("/api/approvals/users", headers=admin_headers)
    assert pending.status_code == 200
    user_id = pending.json()[0]["id"]
    approve = client.post(f"/api/approvals/users/{user_id}/approve", json={"role_ids": []}, headers=admin_headers)
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
    users_route = next(item for item in permissions if item["code"] == "route:users")
    assign = client.put(f"/api/roles/{role_id}/permissions", json={"permission_ids": [users_route["id"]]}, headers=admin_headers)
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
    assert client.post("/api/users", json={}, headers=reader_headers).status_code == 403
