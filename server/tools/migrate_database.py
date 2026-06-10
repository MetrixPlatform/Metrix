from __future__ import annotations

import argparse
from pathlib import Path
import sys

from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.init import sync_database  # noqa: E402
from app.db.session import create_engine_for_url  # noqa: E402
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

    args = parser.parse_args()
    if args.command == "export":
        export_database(args.url, args.out)
    elif args.command == "import":
        import_database(args.url, args.source)
    elif args.command == "copy":
        export_database(args.from_url, args.backup)
        import_database(args.to_url, args.backup)
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


if __name__ == "__main__":
    raise SystemExit(main())
