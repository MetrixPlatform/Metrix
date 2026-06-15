from collections.abc import Iterable
import logging

from fastapi import HTTPException
from fastapi.routing import APIRoute, generate_unique_id
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_session_factory

logger = logging.getLogger(__name__)

LEGACY_OPERATION_ID_TABLE_COLUMNS = {
    "audit_logs": ("action", "target_type", "target_id", "detail", "detail_data"),
    "migration_records": ("`key`", "kind", "target", "detail"),
}


def short_operation_id(route: APIRoute) -> str:
    prefix = (route.tags[0] if route.tags else "").replace("-", "_")
    return f"{prefix}.{route.name}" if prefix else route.name


def normalize_legacy_operation_ids(routes: Iterable[object]) -> None:
    replacements = _legacy_operation_id_replacements(routes)
    if not replacements:
        return
    try:
        with get_session_factory()() as db:
            existing_tables = set(inspect(db.get_bind()).get_table_names())
            for table, columns in LEGACY_OPERATION_ID_TABLE_COLUMNS.items():
                if table not in existing_tables:
                    continue
                for column in columns:
                    for legacy_id, current_id in replacements:
                        db.execute(
                            text(
                                f"UPDATE {table} SET {column} = REPLACE({column}, :legacy_id, :current_id) "
                                f"WHERE {column} LIKE :pattern"
                            ),
                            {"legacy_id": legacy_id, "current_id": current_id, "pattern": f"%{legacy_id}%"},
                        )
            db.commit()
    except HTTPException as exc:
        if exc.status_code != 503:
            raise
    except SQLAlchemyError as exc:
        logger.warning("Skip legacy OpenAPI operation ID normalization: %s", exc)


def _legacy_operation_id_replacements(routes: Iterable[object]) -> tuple[tuple[str, str], ...]:
    replacements: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for route in routes:
        if not isinstance(route, APIRoute):
            continue
        legacy_id = generate_unique_id(route)
        current_id = route.unique_id
        if not legacy_id or not current_id or legacy_id == current_id:
            continue
        pair = (legacy_id, current_id)
        if pair in seen:
            continue
        seen.add(pair)
        replacements.append(pair)
    return tuple(replacements)
