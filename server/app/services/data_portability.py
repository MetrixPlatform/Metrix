from __future__ import annotations

import json
import re
import zipfile
from datetime import date, datetime
from io import BytesIO
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import Base

IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def export_database(db: Session) -> bytes:
    buffer = BytesIO()
    engine = db.get_bind()
    tables = list_database_tables(engine)
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as backup:
        backup.writestr("metadata.json", _metadata(tables, engine.dialect.name))
        for table in tables:
            backup.writestr(f"tables/{table}.json", json.dumps(_table_rows(db, table), ensure_ascii=False, indent=2))
    return buffer.getvalue()


def export_database_to_file(db: Session, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(export_database(db))


def import_database_from_file(engine: Engine, source: Path) -> None:
    with zipfile.ZipFile(source, "r") as backup:
        target_tables = set(list_database_tables(engine))
        tables = [table for table in _backup_tables(backup) if table in target_tables]
        with engine.begin() as conn:
            foreign_keys_disabled = engine.dialect.name == "mysql"
            if foreign_keys_disabled:
                conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
            try:
                for table in reversed(tables):
                    conn.execute(text(f"DELETE FROM `{_safe_identifier(table)}`"))
                for table in tables:
                    rows = json.loads(backup.read(f"tables/{table}.json").decode("utf-8"))
                    if not rows:
                        continue
                    columns = [_safe_identifier(column) for column in rows[0]]
                    insert_sql = text(
                        f"INSERT INTO `{_safe_identifier(table)}` "
                        f"({', '.join(f'`{column}`' for column in columns)}) "
                        f"VALUES ({', '.join(f':{column}' for column in columns)})"
                    )
                    conn.execute(insert_sql, [{column: row.get(column) for column in columns} for row in rows])
            finally:
                if foreign_keys_disabled:
                    conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))


def list_database_tables(engine) -> list[str]:
    existing = set(inspect(engine).get_table_names())
    ordered = [table.name for table in Base.metadata.sorted_tables if table.name in existing]
    remaining = sorted(existing - set(ordered) - {"sqlite_sequence"})
    return ordered + remaining


def _metadata(tables: list[str], database_type: str) -> str:
    payload = {
        "app_name": get_settings().app_name,
        "app_version": get_settings().app_version,
        "database_type": database_type,
        "exported_by": "Metrix",
        "tables": tables,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _backup_tables(backup: zipfile.ZipFile) -> list[str]:
    try:
        metadata = json.loads(backup.read("metadata.json").decode("utf-8"))
        tables = metadata.get("tables")
        if isinstance(tables, list):
            return [item for item in tables if isinstance(item, str) and f"tables/{item}.json" in backup.namelist()]
    except (KeyError, json.JSONDecodeError):
        pass
    return sorted(Path(name).stem for name in backup.namelist() if name.startswith("tables/") and name.endswith(".json"))


def _table_rows(db: Session, table: str) -> list[dict[str, object]]:
    safe_table = _safe_identifier(table)
    rows = db.execute(text(f"SELECT * FROM `{safe_table}`")).mappings().all()
    return [{key: _json_value(value) for key, value in dict(row).items()} for row in rows]


def _safe_identifier(value: str) -> str:
    cleaned = value.replace("`", "")
    if not IDENTIFIER_RE.fullmatch(cleaned):
        raise ValueError(f"Invalid database identifier: {value}")
    return cleaned


def _json_value(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    return value
