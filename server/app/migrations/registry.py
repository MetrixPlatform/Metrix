from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pkgutil import iter_modules

from sqlalchemy import text
from sqlalchemy.engine import Engine

import app.migrations.versions as versions_package

SCHEMA_MIGRATION_KIND = "schema_migration"


@dataclass(frozen=True)
class SchemaMigration:
    revision: str
    down_revision: str | None
    description: str
    upgrade: tuple[str, ...] = ()
    downgrade: tuple[str, ...] = ()


def discover_schema_migrations() -> tuple[SchemaMigration, ...]:
    migrations = []
    for module_info in iter_modules(versions_package.__path__, f"{versions_package.__name__}."):
        module = import_module(module_info.name)
        migration = getattr(module, "MIGRATION", None)
        if isinstance(migration, SchemaMigration):
            migrations.append(migration)
    migrations_tuple = tuple(migrations)
    _validate_migrations(migrations_tuple)
    return _order_migrations(migrations_tuple)


def schema_migration_status(engine: Engine) -> list[dict[str, object]]:
    migrations = discover_schema_migrations()
    applied = _applied_schema_migration_keys(engine)
    return [
        {
            "revision": migration.revision,
            "down_revision": migration.down_revision,
            "description": migration.description,
            "applied": _record_key(migration.revision) in applied,
        }
        for migration in migrations
    ]


def apply_schema_migrations(engine: Engine, target: str | None = None) -> list[str]:
    migrations = discover_schema_migrations()
    if target and target not in {migration.revision for migration in migrations}:
        raise RuntimeError(f"Unknown schema migration target: {target}")
    applied_revisions = []
    with engine.begin() as conn:
        applied = _applied_schema_migration_keys_from_conn(conn)
        for migration in migrations:
            key = _record_key(migration.revision)
            if key not in applied:
                for statement in migration.upgrade:
                    conn.execute(text(statement))
                _record_schema_migration(conn, migration)
                applied_revisions.append(migration.revision)
            if target == migration.revision:
                break
    return applied_revisions


def rollback_schema_migration(engine: Engine, revision: str | None = None) -> str | None:
    migrations_by_revision = {migration.revision: migration for migration in discover_schema_migrations()}
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                "SELECT `key` FROM migration_records "
                "WHERE kind = :kind AND `key` LIKE 'schema:%' ORDER BY applied_at DESC, id DESC"
            ),
            {"kind": SCHEMA_MIGRATION_KIND},
        ).all()
        applied = [row[0].removeprefix("schema:") for row in rows]
        target = revision or (applied[0] if applied else None)
        if target is None:
            return None
        if target not in applied:
            raise RuntimeError(f"Schema migration is not applied: {target}")
        if target != applied[0]:
            raise RuntimeError(f"Only the latest applied schema migration can be rolled back: {applied[0]}")
        migration = migrations_by_revision.get(target)
        if migration is None:
            raise RuntimeError(f"Unknown schema migration revision: {target}")
        if not migration.downgrade:
            raise RuntimeError(f"Schema migration cannot be rolled back automatically: {target}")
        for statement in migration.downgrade:
            conn.execute(text(statement))
        conn.execute(text("DELETE FROM migration_records WHERE `key` = :key"), {"key": _record_key(target)})
        return target


def _order_migrations(migrations: tuple[SchemaMigration, ...]) -> tuple[SchemaMigration, ...]:
    if not migrations:
        return ()
    children_by_parent = {
        migration.down_revision: migration
        for migration in migrations
        if migration.down_revision is not None
    }
    roots = [migration for migration in migrations if migration.down_revision is None]
    ordered = []
    current = roots[0] if roots else None
    while current is not None:
        ordered.append(current)
        current = children_by_parent.get(current.revision)
    if len(ordered) != len(migrations):
        raise RuntimeError("Schema migrations must form a single linear chain")
    return tuple(ordered)


def _validate_migrations(migrations: tuple[SchemaMigration, ...]) -> None:
    revisions = [migration.revision for migration in migrations]
    duplicates = {revision for revision in revisions if revisions.count(revision) > 1}
    if duplicates:
        raise RuntimeError(f"Duplicate schema migration revision: {', '.join(sorted(duplicates))}")
    revision_set = set(revisions)
    roots = [migration for migration in migrations if migration.down_revision is None]
    if migrations and len(roots) != 1:
        raise RuntimeError("Schema migrations must have a single root revision")
    missing = sorted(
        f"{migration.revision}->{migration.down_revision}"
        for migration in migrations
        if migration.down_revision is not None and migration.down_revision not in revision_set
    )
    if missing:
        raise RuntimeError(f"Missing schema migration dependency: {', '.join(missing)}")
    parent_counts: dict[str, int] = {}
    for migration in migrations:
        if migration.down_revision is not None:
            parent_counts[migration.down_revision] = parent_counts.get(migration.down_revision, 0) + 1
    branches = sorted(parent for parent, count in parent_counts.items() if count > 1)
    if branches:
        raise RuntimeError(f"Schema migrations must not branch from revision: {', '.join(branches)}")


def _applied_schema_migration_keys(engine: Engine) -> set[str]:
    with engine.begin() as conn:
        return _applied_schema_migration_keys_from_conn(conn)


def _applied_schema_migration_keys_from_conn(conn) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            text("SELECT `key` FROM migration_records WHERE kind = :kind AND `key` LIKE 'schema:%'"),
            {"kind": SCHEMA_MIGRATION_KIND},
        ).all()
    }


def _record_schema_migration(conn, migration: SchemaMigration) -> None:
    conn.execute(
        text(
            "INSERT INTO migration_records (`key`, kind, target, detail, applied_at) "
            "VALUES (:key, :kind, :target, :detail, CURRENT_TIMESTAMP)"
        ),
        {
            "key": _record_key(migration.revision),
            "kind": SCHEMA_MIGRATION_KIND,
            "target": migration.revision,
            "detail": migration.description,
        },
    )


def _record_key(revision: str) -> str:
    return f"schema:{revision}"
