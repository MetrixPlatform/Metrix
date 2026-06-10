import re
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import bad_request
from app.core.install import default_sqlite_path, is_installed, load_install_config, write_install_config
from app.db.init import create_tables, run_migrations, seed_database, sync_columns, sync_module_states
from app.db.session import create_engine_for_url, reset_engine
from app.schemas.install import InstallDatabaseTestRequest, InstallRequest, MysqlInstallConfig

MYSQL_DATABASE_RE = re.compile(r"^[A-Za-z0-9_]+$")


def test_database_connection(payload: InstallDatabaseTestRequest) -> None:
    database_url = _test_database_url(payload)
    engine = create_engine_for_url(database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise bad_request("error.databaseConnectionFailed", "Database connection failed") from exc
    finally:
        engine.dispose()


def install_system(payload: InstallRequest) -> None:
    if is_installed():
        raise bad_request("error.installed", "System is already initialized")
    database_url = _database_url(payload)
    if payload.database_type == "mysql":
        _create_mysql_database(payload)

    engine = create_engine_for_url(database_url)
    try:
        create_tables(engine)
        run_migrations(engine)
        sync_columns(engine)
        sync_module_states(engine)
        session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
        with session_factory() as db:
            seed_database(db, payload)
    finally:
        engine.dispose()

    write_install_config(payload.database_type, database_url)
    reset_engine()


def installed_database_type() -> str | None:
    if not is_installed():
        return None
    return load_install_config().database_type


def _database_url(payload: InstallRequest) -> str:
    if payload.database_type == "sqlite":
        return _sqlite_url(payload.sqlite_path)
    if payload.mysql is None:
        raise bad_request("error.mysqlConfigRequired", "MySQL connection config is required")
    _guard_mysql_database(payload.mysql.database)
    password = quote_plus(payload.mysql.password)
    username = quote_plus(payload.mysql.username)
    return (
        f"mysql+pymysql://{username}:{password}@{payload.mysql.host}:{payload.mysql.port}/"
        f"{payload.mysql.database}?charset=utf8mb4"
    )


def _test_database_url(payload: InstallDatabaseTestRequest) -> str:
    if payload.database_type == "sqlite":
        return _sqlite_url(payload.sqlite_path)
    if payload.mysql is None:
        raise bad_request("error.mysqlConfigRequired", "MySQL connection config is required")
    _guard_mysql_database(payload.mysql.database)
    return _mysql_server_url(payload.mysql)


def _sqlite_url(sqlite_path: str) -> str:
    path = Path(sqlite_path.strip()) if sqlite_path.strip() else default_sqlite_path()
    if not path.is_absolute():
        path = Path.cwd() / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{path.as_posix()}"


def _create_mysql_database(payload: InstallRequest) -> None:
    if payload.mysql is None:
        raise bad_request("error.mysqlConfigRequired", "MySQL connection config is required")
    mysql = payload.mysql
    _guard_mysql_database(mysql.database)
    engine = create_engine_for_url(_mysql_server_url(mysql))
    try:
        with engine.begin() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{mysql.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
    finally:
        engine.dispose()


def _mysql_server_url(mysql: MysqlInstallConfig) -> str:
    username = quote_plus(mysql.username)
    password = quote_plus(mysql.password)
    return f"mysql+pymysql://{username}:{password}@{mysql.host}:{mysql.port}/?charset=utf8mb4"


def _guard_mysql_database(database: str) -> None:
    if not MYSQL_DATABASE_RE.fullmatch(database):
        raise bad_request("error.mysqlDatabaseNameInvalid", "MySQL database name can only contain letters, numbers, and underscores")
