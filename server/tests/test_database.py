import time
from pathlib import Path

from sqlalchemy import create_engine, text

from app.core.security import decrypt_secret, encrypt_secret
from test_auth_rbac import create_client, install_sqlite, login


def make_target_db(path: Path) -> None:
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, age INTEGER)"))
        conn.execute(text("INSERT INTO people (name, age) VALUES ('Alice', 20), ('Bob', 30)"))
    engine.dispose()


def create_sqlite_connection(conn_id: str, target_path: Path) -> int:
    from app.core.install import load_install_config

    engine = create_engine(load_install_config().database_url)
    encrypted = encrypt_secret("unused")
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO db_connections "
                "(conn_id, name, db_type, host, port, username, password_encrypted, default_database, is_shared, is_active, created_by, created_at, updated_at) "
                "VALUES (:conn_id, :name, 'sqlite', :host, 0, 'sqlite', :password, '', 1, 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
            ),
            {"conn_id": conn_id, "name": "SQLite Target", "host": str(target_path), "password": encrypted},
        )
        connection_id = conn.execute(text("SELECT id FROM db_connections WHERE conn_id = :conn_id"), {"conn_id": conn_id}).scalar_one()
    engine.dispose()
    assert decrypt_secret(encrypted) == "unused"
    return connection_id


def test_database_metadata_query_rows_and_export(tmp_path, monkeypatch):
    client = create_client(tmp_path, monkeypatch)
    payload = install_sqlite(client, tmp_path)
    headers = login(client, payload["admin_username"], payload["admin_password"])
    target_path = tmp_path / "target.db"
    make_target_db(target_path)
    create_sqlite_connection("db_sqlite_test", target_path)

    schemas = client.get("/api/databases/db_sqlite_test/schemas", headers=headers)
    assert schemas.status_code == 200
    assert schemas.json() == [{"name": "main"}]

    tables = client.get("/api/databases/db_sqlite_test/tables", headers=headers)
    assert tables.status_code == 200
    assert {"name": "people"} in tables.json()

    table_data = client.get("/api/databases/db_sqlite_test/table-data?table=people&page_size=10", headers=headers)
    assert table_data.status_code == 200
    assert table_data.json()["total"] == 2
    assert table_data.json()["primary_keys"] == ["id"]

    selected = client.post("/api/databases/db_sqlite_test/query", json={"sql": "SELECT name FROM people ORDER BY id"}, headers=headers)
    assert selected.status_code == 200
    assert [row["name"] for row in selected.json()["rows"]] == ["Alice", "Bob"]

    created = client.post(
        "/api/databases/db_sqlite_test/table-rows",
        json={"table": "people", "values": {"name": "Cara", "age": 25}},
        headers=headers,
    )
    assert created.status_code == 200

    updated = client.put(
        "/api/databases/db_sqlite_test/table-rows",
        json={"table": "people", "keys": {"id": 3}, "values": {"name": "Cara", "age": 26}},
        headers=headers,
    )
    assert updated.status_code == 200

    script = client.post(
        "/api/databases/db_sqlite_test/run-script",
        json={"content": "SELECT COUNT(*) AS total FROM people; UPDATE people SET age = age + 1 WHERE id = 3;"},
        headers=headers,
    )
    assert script.status_code == 200
    assert len(script.json()["results"]) == 2

    submitted = client.post(
        "/api/databases/db_sqlite_test/export",
        json={"format": "csv", "tables": ["people"]},
        headers=headers,
    )
    assert submitted.status_code == 200
    job_id = submitted.json()["job_id"]
    job = wait_job(client, headers, job_id)
    assert job["status"] == "success"
    assert job["row_count"] == 3

    submitted_later = client.post(
        "/api/databases/db_sqlite_test/export",
        json={"format": "csv", "tables": ["people"]},
        headers=headers,
    )
    assert submitted_later.status_code == 200
    later_job_id = submitted_later.json()["job_id"]
    later_job = wait_job(client, headers, later_job_id)
    assert later_job["status"] == "success"

    jobs_asc = client.get("/api/data-jobs?sort_order=ascend", headers=headers)
    assert jobs_asc.status_code == 200
    assert [item["job_id"] for item in jobs_asc.json()["items"][:2]] == [job_id, later_job_id]

    jobs_desc = client.get("/api/data-jobs?sort_order=descend", headers=headers)
    assert jobs_desc.status_code == 200
    assert [item["job_id"] for item in jobs_desc.json()["items"][:2]] == [later_job_id, job_id]

    download = client.get(f"/api/data-jobs/{job_id}/download", headers=headers)
    assert download.status_code == 200
    assert b"Alice" in download.content


def wait_job(client, headers, job_id: str):
    for _ in range(30):
        response = client.get(f"/api/data-jobs/{job_id}", headers=headers)
        assert response.status_code == 200
        payload = response.json()
        if payload["status"] in {"success", "failed"}:
            return payload
        time.sleep(0.1)
    raise AssertionError("data job did not finish")
