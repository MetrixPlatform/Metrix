from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import sys

from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.init import run_module_uninstall, sync_database  # noqa: E402
from app.db.session import create_engine_for_url  # noqa: E402
from app.migrations import apply_schema_migrations, rollback_schema_migration, schema_migration_status  # noqa: E402
from app.services.data_portability import export_database_to_file, import_database_from_file  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Export, import, or copy Metrix database data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export a database to a portable zip package.")
    export_parser.add_argument("--url", required=True, help="Source SQLAlchemy database URL.")
    export_parser.add_argument("--out", required=True, type=Path, help="Target zip path.")

    import_parser = subparsers.add_parser("import", help="Import a portable zip package into a database.")
    import_parser.add_argument("--url", required=True, help="Target SQLAlchemy database URL.")
    import_parser.add_argument("--in", dest="source", required=True, type=Path, help="Source zip path.")

    copy_parser = subparsers.add_parser("copy", help="Copy data between two database URLs through a portable package.")
    copy_parser.add_argument("--from-url", required=True, help="Source SQLAlchemy database URL.")
    copy_parser.add_argument("--to-url", required=True, help="Target SQLAlchemy database URL.")
    copy_parser.add_argument("--backup", required=True, type=Path, help="Portable backup zip path kept for rollback.")

    status_parser = subparsers.add_parser("schema-status", help="Show explicit schema migration status.")
    status_parser.add_argument("--url", required=True, help="SQLAlchemy database URL.")

    apply_parser = subparsers.add_parser("schema-apply", help="Apply explicit schema migrations.")
    apply_parser.add_argument("--url", required=True, help="SQLAlchemy database URL.")
    apply_parser.add_argument("--target", help="Stop after this revision.")

    rollback_parser = subparsers.add_parser("schema-rollback", help="Rollback one explicit schema migration.")
    rollback_parser.add_argument("--url", required=True, help="SQLAlchemy database URL.")
    rollback_parser.add_argument("--revision", help="Revision to rollback. Defaults to the latest applied revision.")

    new_parser = subparsers.add_parser("schema-new", help="Create an empty explicit schema migration file.")
    new_parser.add_argument("name", help="Human-readable migration name, e.g. add task indexes.")
    new_parser.add_argument("--down-revision", help="Parent revision. Defaults to the latest known revision.")

    uninstall_parser = subparsers.add_parser("module-uninstall", help="Run a module uninstall hook and mark it uninstalled.")
    uninstall_parser.add_argument("--url", required=True, help="SQLAlchemy database URL.")
    uninstall_parser.add_argument("--module", required=True, help="Module key, e.g. demo_crud.")
    uninstall_parser.add_argument("--backup", type=Path, help="Optional portable backup zip written before uninstall.")

    args = parser.parse_args()
    if args.command == "export":
        export_database(args.url, args.out)
    elif args.command == "import":
        import_database(args.url, args.source)
    elif args.command == "copy":
        export_database(args.from_url, args.backup)
        import_database(args.to_url, args.backup)
    elif args.command == "schema-status":
        show_schema_status(args.url)
    elif args.command == "schema-apply":
        apply_schema(args.url, args.target)
    elif args.command == "schema-rollback":
        rollback_schema(args.url, args.revision)
    elif args.command == "schema-new":
        create_schema_revision(args.name, args.down_revision)
    elif args.command == "module-uninstall":
        uninstall_module(args.url, args.module, args.backup)
    return 0


def export_database(database_url: str, target: Path) -> None:
    engine = create_engine_for_url(database_url)
    try:
        sync_database(engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        with session_factory() as db:
            export_database_to_file(db, target)
    finally:
        engine.dispose()


def import_database(database_url: str, source: Path) -> None:
    engine = create_engine_for_url(database_url)
    try:
        sync_database(engine)
        import_database_from_file(engine, source)
        sync_database(engine)
    finally:
        engine.dispose()


def show_schema_status(database_url: str) -> None:
    engine = create_engine_for_url(database_url)
    try:
        sync_database(engine)
        for item in schema_migration_status(engine):
            marker = "applied" if item["applied"] else "pending"
            print(f"{marker:8} {item['revision']} {item['description']}")
    finally:
        engine.dispose()


def apply_schema(database_url: str, target: str | None) -> None:
    engine = create_engine_for_url(database_url)
    try:
        sync_database(engine)
        revisions = apply_schema_migrations(engine, target)
        if revisions:
            print("Applied schema migrations: " + ", ".join(revisions))
        else:
            print("No pending schema migrations")
    finally:
        engine.dispose()


def rollback_schema(database_url: str, revision: str | None) -> None:
    engine = create_engine_for_url(database_url)
    try:
        sync_database(engine)
        reverted = rollback_schema_migration(engine, revision)
        if reverted:
            print(f"Rolled back schema migration: {reverted}")
        else:
            print("No applied schema migrations to rollback")
    finally:
        engine.dispose()


def create_schema_revision(name: str, down_revision: str | None) -> None:
    from app.migrations.registry import discover_schema_migrations

    migrations = discover_schema_migrations()
    parent = down_revision if down_revision is not None else (migrations[-1].revision if migrations else None)
    revision = f"{datetime.utcnow():%Y%m%d%H%M%S}_{slugify(name)}"
    target = ROOT_DIR / "app" / "migrations" / "versions" / f"{revision}.py"
    target.write_text(
        "\n".join(
            [
                "from app.migrations.registry import SchemaMigration",
                "",
                "MIGRATION = SchemaMigration(",
                f'    revision="{revision}",',
                f'    down_revision={parent!r},',
                f'    description="{name}",',
                "    upgrade=(",
                "        # Add SQL statements here.",
                "    ),",
                "    downgrade=(",
                "        # Add rollback SQL statements here.",
                "    ),",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Created schema migration: {target.relative_to(ROOT_DIR)}")


def uninstall_module(database_url: str, module_key: str, backup_path: Path | None) -> None:
    if backup_path is not None:
        export_database(database_url, backup_path)
    engine = create_engine_for_url(database_url)
    try:
        sync_database(engine)
        run_module_uninstall(engine, module_key)
        print(f"Module uninstalled: {module_key}")
    finally:
        engine.dispose()


def slugify(value: str) -> str:
    output = "".join(char.lower() if char.isalnum() else "_" for char in value.strip())
    return "_".join(part for part in output.split("_") if part) or "migration"


if __name__ == "__main__":
    raise SystemExit(main())
